import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

/**
 * jev-router — deterministic model routing for the harness.
 *
 * The `jev_decide` tool is advisory: it returns a decision but never touches the
 * model. This extension closes that gap. It turns Jev's judgment into an actual
 * `pi.setModel()` call at two enforcement points:
 *
 *   1. `before_agent_start` — classifies the user prompt before the turn starts,
 *      so the correct lane is active before any tokens are spent.
 *   2. `tool_result` — watches the result of the agent's own `jev_decide` call and
 *      escalates the NEXT turn when the decision is ESCALATE.
 *
 * Mapping (from AGENTS.md):
 *   SMALL / MEDIUM / HIGH → BASIC_MODEL (low / medium / high reasoning)
 *   ESCALATE              → PRO_MODEL   (high reasoning)
 *
 * Jev runs through TypeSafe via pi's classifier registry (`typesafe/jev-latest`),
 * authenticated with TYPESAFE_API_KEY. No OpenRouter dependency.
 *
 * Every decision and every applied switch is recorded with `pi.appendEntry`, so
 * `scripts/audit_escalation.py` can prove, from the session JSONL, that the model
 * really changed. Jev failures never break a turn: the current model is kept.
 */

const JEV_PROVIDER = "typesafe";
const JEV_MODEL = "jev-latest";

const MIN_CONF = (() => {
  const n = Number(process.env.JEV_MIN_CONFIDENCE ?? "0.7");
  return Number.isFinite(n) && n >= 0 && n <= 1 ? n : 0.7;
})();

const ROUTES = {
  SMALL: "Small, localized change with clear requirements and minimal risk.",
  MEDIUM:
    "Moderate implementation involving multiple related changes or ordinary debugging.",
  HIGH: "Complex implementation, substantial uncertainty, difficult debugging, or cross-module changes.",
  ESCALATE:
    "Requires a stronger coding model due to security-sensitive changes or unresolved architectural uncertainty.",
} as const;

type Lane = keyof typeof ROUTES;
// AGENTS.md lanes only ever use low / medium / high reasoning.
type ThinkingLevel = "low" | "medium" | "high";

type RouteDecision =
  | { lane: Lane; confidence: number; withheld: false }
  | { lane: Lane; confidence: number; withheld: true };

function laneTarget(lane: Lane): { ref?: string; thinking: ThinkingLevel } {
  if (lane === "ESCALATE") {
    return { ref: process.env.PRO_MODEL, thinking: "high" };
  }
  return {
    ref: process.env.BASIC_MODEL,
    thinking: lane === "HIGH" ? "high" : lane === "MEDIUM" ? "medium" : "low",
  };
}

/**
 * Resolves a routing target. Accepts `provider/model-id`; a bare `model-id`
 * (as the harness sets BASIC_MODEL / PRO_MODEL) uses `fallbackProvider`, taken
 * from the active model.
 */
function parseRef(
  ref?: string,
  fallbackProvider?: string,
): { provider: string; id: string } | undefined {
  if (!ref) return undefined;
  const i = ref.indexOf("/");
  if (i > 0 && i < ref.length - 1) {
    return { provider: ref.slice(0, i), id: ref.slice(i + 1) };
  }
  if (i === -1 && fallbackProvider) {
    return { provider: fallbackProvider, id: ref };
  }
  return undefined;
}

async function askRoute(ctx: any, prompt: string): Promise<RouteDecision | null> {
  const jev = ctx.modelRegistry.findOfType("classifier", JEV_PROVIDER, JEV_MODEL);
  if (!jev) return null;

  const outcome = await ctx.modelRegistry.classify(
    jev,
    {
      state: { task: prompt },
      questions: {
        decision: {
          type: "choice",
          instructions:
            "Classify the software task. Choose the lowest sufficient complexity lane. Select ESCALATE only when the task requires a stronger coding model.",
          criteria: ROUTES,
        },
      },
    },
    { signal: AbortSignal.timeout(20_000) },
  );
  if (outcome.stopReason !== "stop") return null;

  const answer: any = outcome.answers?.decision;
  if (answer?.type !== "choice" || !(answer.choice in ROUTES)) return null;
  const confidence = typeof answer.confidence === "number" ? answer.confidence : 0;
  const lane = answer.choice as Lane;
  return confidence >= MIN_CONF
    ? { lane, confidence, withheld: false }
    : { lane, confidence, withheld: true };
}

async function applyLane(
  pi: ExtensionAPI,
  ctx: any,
  lane: Lane,
  phase: string,
  confidence?: number,
): Promise<void> {
  const target = laneTarget(lane);
  const ref = parseRef(target.ref, ctx.model?.provider);
  const label = lane === "ESCALATE" ? "PRO_MODEL" : "BASIC_MODEL";
  const meta = { phase, lane, confidence, applied: false } as Record<string, unknown>;

  if (!ref) {
    ctx.ui.notify(`jev-router: ${lane} — ${label} não configurado; mantendo modelo`, "warning");
    pi.appendEntry("jev-router", { ...meta, reason: "target-unset" });
    return;
  }

  const model = ctx.modelRegistry.find(ref.provider, ref.id);
  if (!model) {
    ctx.ui.notify(`jev-router: ${ref.provider}/${ref.id} não encontrado; mantendo modelo`, "warning");
    pi.appendEntry("jev-router", { ...meta, target: `${ref.provider}/${ref.id}`, reason: "model-not-found" });
    return;
  }

  if (ctx.model?.provider === model.provider && ctx.model?.id === model.id) {
    pi.appendEntry("jev-router", { ...meta, target: `${ref.provider}/${ref.id}`, reason: "already-active" });
    return;
  }

  const ok = await pi.setModel(model);
  if (!ok) {
    ctx.ui.notify(`jev-router: sem auth para ${ref.provider}/${ref.id}; mantendo modelo`, "error");
    pi.appendEntry("jev-router", { ...meta, target: `${ref.provider}/${ref.id}`, reason: "auth-missing" });
    return;
  }

  pi.setThinkingLevel(target.thinking);
  ctx.ui.notify(
    `jev-router: ${lane} (${phase}) → ${ref.provider}/${ref.id}:${target.thinking}`,
    "info",
  );
  pi.appendEntry("jev-router", {
    ...meta, target: `${ref.provider}/${ref.id}`, thinking: target.thinking, applied: true,
  });
}

export default function (pi: ExtensionAPI) {
  // (1) Initial routing — guarantees the lane before the turn spends tokens.
  pi.on("before_agent_start", async (event, ctx) => {
    if (!event.prompt.trim()) return;
    try {
      const decision = await askRoute(ctx, event.prompt);
      if (!decision) return;
      if (decision.withheld) {
        pi.appendEntry("jev-router", {
          phase: "route",
          lane: decision.lane,
          confidence: decision.confidence,
          applied: false,
          reason: "low-confidence",
        });
        return;
      }
      await applyLane(
        pi,
        ctx,
        decision.lane,
        `route conf ${Math.round(decision.confidence * 100)}%`,
        decision.confidence,
      );
    } catch (error) {
      ctx.ui.notify(`jev-router: falha na rota; mantendo modelo (${error})`, "error");
    }
  });

  // (2) In-loop escalation — reacts to the agent's own jev_decide result.
  pi.on("tool_result", async (event, ctx) => {
    if (event.toolName !== "jev_decide") return;
    const details: any = event.details;
    if (details?.status === "accepted" && details?.decision === "ESCALATE") {
      const confidence = details.confidence ?? 0;
      await applyLane(
        pi,
        ctx,
        "ESCALATE",
        `next_action conf ${Math.round(confidence * 100)}%`,
        confidence,
      );
    }
  });
}
