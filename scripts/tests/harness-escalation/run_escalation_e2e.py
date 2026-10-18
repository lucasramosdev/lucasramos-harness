#!/usr/bin/env python3
"""End-to-end escalation test: run pi headless on calibrated prompts and prove,
from the resulting session JSONL, that jev-router switched the model for real.

Scenarios:
  1. route-escalate        complex/security prompt starting on BASIC → must end on PRO
  2. route-simple          trivial prompt starting on PRO         → must end on BASIC
  3. next-action-escalate  agent calls jev_decide (ESCALATE)       → next turn on PRO

Requires: OPENROUTER_API_KEY, BASIC_MODEL, PRO_MODEL in the environment.
Run from the project root. Sessions and the audit verdict are printed at the end.
"""

from __future__ import annotations

import glob
import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
PROVIDER = "deepseek"
AUDIT = PROJECT / "scripts" / "audit_escalation.py"
EVIDENCE_FILE = PROJECT / ".ai" / "jev-e2e" / "evidence.txt"

EVIDENCE_TEXT = (
    "Tres tentativas de correcao falharam; os testes de isolamento entre tenants "
    "continuam falhando (tenant A acessa dados do tenant B); codigo sensivel a "
    "seguranca; causa raiz desconhecida e incerteza arquitetural."
)

SCENARIOS = [
    {
        "name": "route-escalate",
        "start": os.environ.get("BASIC_MODEL", "deepseek-flash"),
        "tools": ["--no-tools"],
        "prompt": (
            "Corrija o vazamento intermitente de dados entre tenants que so ocorre em "
            "producao sob carga; duas tentativas anteriores de correcao falharam, a area "
            "e sensivel a seguranca e a causa raiz ainda e desconhecida."
        ),
    },
    {
        "name": "route-simple",
        "start": os.environ.get("PRO_MODEL", "deepseek-v4-pro"),
        "tools": ["--no-tools"],
        "prompt": "Renomeie a variavel x para total no arquivo src/utils.ts.",
    },
    {
        "name": "next-action-escalate",
        "start": os.environ.get("BASIC_MODEL", "deepseek-flash"),
        "tools": ["--tools", "jev_decide"],
        "prompt": (
            "Chame a ferramenta jev_decide exatamente uma vez com kind='next_action', "
            "task='Corrigir falha de autorizacao entre tenants', evidence='Tres tentativas "
            "de correcao falharam; os testes de isolamento entre tenants continuam falhando; "
            "codigo sensivel a seguranca; causa raiz desconhecida'. Nao use outras ferramentas. "
            "Depois responda OK."
        ),
    },
    {
        # Isolates the tool_result escalation path: the prompt itself is generic
        # (routes to BASIC), the escalation evidence lives in a file the agent reads.
        "name": "tool-escalate-isolated",
        "start": os.environ.get("BASIC_MODEL", "deepseek-flash"),
        "tools": ["--tools", "read,jev_decide"],
        "prompt": (
            f"Leia o arquivo {EVIDENCE_FILE} com a ferramenta read. Em seguida chame a "
            "ferramenta jev_decide exatamente uma vez com kind='next_action', "
            "task='Corrigir falha de autorizacao entre tenants' e evidence igual ao "
            "conteudo exato do arquivo lido. Nao edite arquivos. Depois responda OK."
        ),
    },
]


def newest_session(directory: Path, before: set[str]) -> Path | None:
    files = set(glob.glob(str(directory / "*.jsonl")))
    new = sorted(files - before, key=os.path.getmtime)
    if new:
        return Path(new[-1])
    files_all = sorted(files, key=os.path.getmtime)
    return Path(files_all[-1]) if files_all else None


def main() -> int:
    for var in ("OPENROUTER_API_KEY", "BASIC_MODEL", "PRO_MODEL"):
        if not os.environ.get(var):
            print(f"{var} precisa estar definido no ambiente.", file=sys.stderr)
            return 2

    workdir = PROJECT / ".ai" / "jev-e2e"
    workdir.mkdir(parents=True, exist_ok=True)
    EVIDENCE_FILE.write_text(EVIDENCE_TEXT, encoding="utf-8")

    env = dict(os.environ)
    env.pop("PI_SESSION_FILE", None)
    env.pop("PI_SESSION_ID", None)

    sessions: list[Path] = []
    for sc in SCENARIOS:
        before = set(glob.glob(str(workdir / "*.jsonl")))
        cmd = [
            "pi", "-p",
            "--session-dir", str(workdir),
            "--name", sc["name"],
            "--provider", PROVIDER,
            "--model", sc["start"],
            "--approve",
            "--no-skills",
            *sc["tools"],
            sc["prompt"],
        ]
        print(f"\n### cenário {sc['name']}: start={sc['start']} tools={sc['tools']}")
        proc = subprocess.run(cmd, cwd=PROJECT, env=env, capture_output=True, text=True, timeout=600)
        session = newest_session(workdir, before)
        if session is None:
            print("  !! sessão não encontrada", file=sys.stderr)
            print(proc.stderr[-400:], file=sys.stderr)
            continue
        sessions.append(session)
        print(f"  sessão: {session}")

    if not sessions:
        return 2

    print("\n" + "=" * 70)
    print("AUDITORIA")
    failed = 0
    for session in sessions:
        r = subprocess.run(
            [sys.executable, str(AUDIT), "--session", str(session)],
            cwd=PROJECT, env=env, capture_output=True, text=True,
        )
        print(r.stdout)
        if r.returncode != 0:
            failed += 1
            if r.stderr.strip():
                print(r.stderr, file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
