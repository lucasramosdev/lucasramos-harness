#!/usr/bin/env python3
"""Acceptance audit for Jev escalation: prove the model actually changed.

`jev_decide` is advisory and never switches the model. `.pi/extensions/jev-router.ts`
turns its decisions into real `pi.setModel()` calls. This script reads one or more
pi session JSONL files and verifies the invariant that makes the routing a guarantee:

    after every applied ESCALATE decision, the next assistant turn must run on
    PRO_MODEL; after every applied non-escalation lane, it must run on BASIC_MODEL.

It also independently checks every accepted `jev_decide` result of the session, so a
missing jev-router entry is still caught.

Model names come from the environment (BASIC_MODEL / PRO_MODEL). Either a bare id
(`deepseek-flash`) or `provider/id` is accepted.

Usage:
    python3 scripts/harness-escalation/audit_escalation.py --session path/to/session.jsonl
    python3 scripts/harness-escalation/audit_escalation.py --dir /tmp/jev_e2e --latest
    python3 scripts/harness-escalation/audit_escalation.py --dir /tmp/jev_e2e --all
Exit code: 0 if all invariants hold, 1 otherwise.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

NON_ESCALATION = {"SMALL", "MEDIUM", "HIGH"}


def basename(ref: str | None) -> str | None:
    if not ref:
        return None
    return ref.split("/")[-1].strip() or None


def parse_jev_text(text: str) -> dict | None:
    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    return obj if isinstance(obj, dict) else None


def timeline(path: str) -> list[dict]:
    events: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = entry.get("type")
            ts = entry.get("timestamp", "")
            if etype == "model_change":
                events.append({
                    "kind": "model_change",
                    "ts": ts,
                    "model": basename(entry.get("modelId")),
                    "provider": entry.get("provider"),
                })
            elif etype == "thinking_level_change":
                events.append({"kind": "thinking", "ts": ts, "level": entry.get("thinkingLevel")})
            elif etype == "custom" and entry.get("customType") == "jev-router":
                data = entry.get("data") or {}
                events.append({
                    "kind": "router_decision",
                    "ts": ts,
                    "phase": data.get("phase"),
                    "lane": data.get("lane"),
                    "confidence": data.get("confidence"),
                    "applied": data.get("applied"),
                    "reason": data.get("reason"),
                    "target": data.get("target"),
                })
            elif etype == "message":
                msg = entry.get("message") or {}
                role = msg.get("role")
                if role == "assistant":
                    calls = [
                        c for c in (msg.get("content") or [])
                        if isinstance(c, dict) and c.get("type") == "toolCall"
                    ]
                    events.append({
                        "kind": "assistant",
                        "ts": ts,
                        "model": basename(msg.get("model")),
                        "provider": msg.get("provider"),
                        "tools": [c.get("name") for c in calls],
                    })
                elif role == "toolResult" and msg.get("toolName") == "jev_decide":
                    text = ""
                    content = msg.get("content")
                    if isinstance(content, list) and content and isinstance(content[0], dict):
                        text = content[0].get("text", "")
                    parsed = parse_jev_text(text)
                    events.append({
                        "kind": "jev_result",
                        "ts": ts,
                        "status": (parsed or {}).get("status"),
                        "decision": (parsed or {}).get("decision"),
                        "confidence": (parsed or {}).get("confidence"),
                    })
                elif role == "user":
                    text = msg.get("content")
                    if isinstance(text, list):
                        text = " ".join(
                            c.get("text", "") for c in text if isinstance(c, dict)
                        )
                    events.append({"kind": "user", "ts": ts, "text": str(text or "")[:90]})
    return events


def next_assistant(events: list[dict], start: int) -> dict | None:
    for ev in events[start + 1:]:
        if ev["kind"] == "assistant":
            return ev
    return None


def audit(path: str, basic: str | None, pro: str | None) -> list[str]:
    events = timeline(path)
    failures: list[str] = []
    checks = 0

    for i, ev in enumerate(events):
        if ev["kind"] == "router_decision" and ev.get("applied"):
            lane = ev.get("lane")
            nxt = next_assistant(events, i)
            checks += 1
            expected = pro if lane == "ESCALATE" else basic
            if nxt is None:
                failures.append(f"[{ev['ts']}] {lane}: nenhum turno de assistant após a decisão")
            elif expected and nxt["model"] != expected:
                failures.append(
                    f"[{ev['ts']}] {lane}: esperado {expected}, turno rodou em {nxt['model']}"
                )
        elif ev["kind"] == "jev_result" and ev.get("status") == "accepted" and ev.get("decision") == "ESCALATE":
            nxt = next_assistant(events, i)
            checks += 1
            if nxt is None:
                failures.append(f"[{ev['ts']}] ESCALATE (tool): nenhum turno após o resultado")
            elif pro and nxt["model"] != pro:
                failures.append(
                    f"[{ev['ts']}] ESCALATE (tool): esperado {pro}, turno rodou em {nxt['model']}"
                )
    if checks == 0:
        failures.append("nenhuma decisão aplicada encontrada — a extensão jev-router não rodou?")
    return failures


def print_timeline(path: str, events: list[dict]) -> None:
    print(f"\n  sessão: {path}")
    for ev in events:
        ts = ev["ts"][11:19] if ev.get("ts") else "--:--:--"
        if ev["kind"] == "user":
            print(f"    {ts}  USER      {ev['text']}")
        elif ev["kind"] == "assistant":
            tools = ",".join(t for t in ev["tools"] if t) or "-"
            print(f"    {ts}  ASSISTANT model={ev['model']} tools={tools}")
        elif ev["kind"] == "model_change":
            print(f"    {ts}  MODEL→    {ev['provider']}/{ev['model']}")
        elif ev["kind"] == "thinking":
            print(f"    {ts}  THINKING  {ev['level']}")
        elif ev["kind"] == "router_decision":
            status = "APLICADO" if ev.get("applied") else f"retido({ev.get('reason')})"
            print(
                f"    {ts}  ROUTER    {ev.get('phase')} lane={ev.get('lane')} "
                f"conf={ev.get('confidence')} {status}"
            )
        elif ev["kind"] == "jev_result":
            print(
                f"    {ts}  JEV       status={ev.get('status')} "
                f"decision={ev.get('decision')} conf={ev.get('confidence')}"
            )


def resolve_targets(args) -> list[str]:
    if args.session:
        return [args.session]
    files = sorted(glob.glob(os.path.join(args.dir, "*.jsonl")), key=os.path.getmtime)
    if not files:
        print(f"nenhuma sessão .jsonl em {args.dir}", file=sys.stderr)
        sys.exit(2)
    if args.all:
        return files
    return [files[-1]]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Jev escalation model switching.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--session", help="path to one session JSONL")
    src.add_argument("--dir", help="directory containing session JSONL files")
    parser.add_argument("--latest", action="store_true", help="newest session in --dir (default)")
    parser.add_argument("--all", action="store_true", help="all sessions in --dir")
    args = parser.parse_args()

    basic = basename(os.environ.get("BASIC_MODEL"))
    pro = basename(os.environ.get("PRO_MODEL"))
    if not basic or not pro:
        print("BASIC_MODEL e PRO_MODEL precisam estar definidos no ambiente.", file=sys.stderr)
        return 2

    print(f"BASIC_MODEL={basic}  PRO_MODEL={pro}")
    targets = resolve_targets(args)
    total_failures: list[str] = []
    for path in targets:
        events = timeline(path)
        print_timeline(path, events)
        fails = audit(path, basic, pro)
        if fails:
            print("    RESULTADO: FAIL")
            for f in fails:
                print(f"      - {f}")
        else:
            print("    RESULTADO: PASS")
        total_failures.extend(fails)

    print("\n" + "=" * 70)
    if total_failures:
        print(f"AUDIT FAIL — {len(total_failures)} violação(ões); o modelo NÃO foi garantido.")
        return 1
    print(f"AUDIT PASS — {len(targets)} sessão(ões): todo ESCALATE foi seguido do PRO_MODEL.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
