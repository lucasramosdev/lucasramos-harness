import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "@sinclair/typebox";

const JEV_PROVIDER = "typesafe";
const JEV_MODEL = "jev-latest";
const ROUTES = {
  SMALL: "Small, localized change with clear requirements and minimal risk.",
  MEDIUM: "Moderate implementation involving multiple related changes or ordinary debugging.",
  HIGH: "Complex implementation, substantial uncertainty, difficult debugging, or cross-module changes.",
  ESCALATE: "Requires a stronger coding model due to security-sensitive changes or unresolved architectural uncertainty.",
} as const;
const ACTIONS = {
  CONTINUE: "Proceed with the current implementation plan; outstanding work remains.",
  RETRY: "Revise the implementation using concrete failure evidence, then rerun checks.",
  VERIFY: "Run missing deterministic checks or inspect additional evidence before deciding.",
  ESCALATE: "Escalate to a stronger coding model because the current approach is blocked or insufficient.",
  COMPLETE: "All requested behavior is implemented, required deterministic checks passed, and no unresolved issues remain.",
} as const;

type DecisionKind = "route" | "next_action";

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "jev_decide",
    label: "Jev Decision",
    description: "Request a bounded Jev decision via TypeSafe. Use route before implementation or next_action after inspecting diff and deterministic verification. Never substitute this for tests, build, lint, or type checking. A decision is advisory, not proof of correctness.",
    parameters: Type.Object({
      kind: Type.Union([Type.Literal("route"), Type.Literal("next_action")]),
      task: Type.String({ minLength: 1, maxLength: 12000, description: "Original user request and relevant constraints; redact secrets." }),
      evidence: Type.Optional(Type.String({ maxLength: 16000, description: "Concise diff summary, checks and results, unresolved issues, and prior attempts. Required for next_action." })),
      current_lane: Type.Optional(Type.String({ maxLength: 100, description: "Current coding model/reasoning lane, if relevant." })),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      if (params.kind === "next_action" && !params.evidence?.trim()) {
        return { content: [{ type: "text", text: "JEV_SKIPPED: next_action requires concrete verification evidence. Inspect diff and run relevant checks first." }], details: { status: "skipped" } };
      }
      const kind = params.kind as DecisionKind;
      const criteria = kind === "route" ? ROUTES : ACTIONS;
      const instructions = kind === "route"
        ? "Classify the software task. Choose the lowest sufficient complexity lane. Select ESCALATE only when the task requires a stronger coding model."
        : "Choose the next action based on the supplied evidence. Do not claim COMPLETE if tests failed, checks are missing, scope is unresolved, or the requested behavior is not demonstrated. Prefer VERIFY when evidence is insufficient.";
      const state = {
        task: params.task,
        ...(params.current_lane ? { current_lane: params.current_lane } : {}),
        ...(params.evidence ? { evidence: params.evidence } : {}),
      };

      const jev = ctx.modelRegistry.findOfType("classifier", JEV_PROVIDER, JEV_MODEL);
      if (!jev) {
        return { content: [{ type: "text", text: "JEV_UNAVAILABLE: TypeSafe classifier typesafe/jev-latest is not available. Check TYPESAFE_API_KEY. Do not claim Jev made a decision." }], details: { status: "unavailable" } };
      }

      const timeout = AbortSignal.timeout(20_000);
      const abort = signal ? AbortSignal.any([signal, timeout]) : timeout;
      try {
        const outcome = await ctx.modelRegistry.classify(
          jev,
          { state, questions: { decision: { type: "choice", instructions, criteria } } },
          { signal: abort },
        );
        if (outcome.stopReason !== "stop") {
          const reason = signal?.aborted ? "Request cancelled" : outcome.stopReason === "aborted" ? "Request cancelled" : outcome.errorMessage ?? "TypeSafe returned no answer";
          return { content: [{ type: "text", text: `JEV_UNAVAILABLE: ${reason}. No decision was obtained.` }], details: { status: "unavailable" } };
        }
        const answer: any = outcome.answers?.decision;
        if (answer?.type !== "choice" || !answer.choice || !(answer.choice in criteria) || typeof answer.confidence !== "number" || !Number.isFinite(answer.confidence) || answer.confidence < 0 || answer.confidence > 1) {
          throw new Error("Invalid or incomplete choice answer");
        }
        const threshold = Number(process.env.JEV_MIN_CONFIDENCE ?? "0.7");
        const minConfidence = Number.isFinite(threshold) && threshold >= 0 && threshold <= 1 ? threshold : 0.7;
        const accepted = answer.confidence >= minConfidence;
        const result = {
          status: accepted ? "accepted" : "low_confidence",
          kind,
          decision: accepted ? answer.choice : null,
          suggested_choice: answer.choice,
          confidence: answer.confidence,
          min_confidence: minConfidence,
          probabilities: answer.probabilities,
          model: `${outcome.provider}/${outcome.model}`,
          guidance: accepted ? "Advisory decision; independently enforce verification and scope requirements." : "Do not act on this choice automatically. Gather more evidence or request human review.",
        };
        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }], details: result };
      } catch (error) {
        const reason = signal?.aborted ? "Request cancelled" : error instanceof Error && error.name === "TimeoutError" ? "Request timed out" : "Network or response validation failure";
        return { content: [{ type: "text", text: `JEV_UNAVAILABLE: ${reason}. No decision was obtained.` }], details: { status: "unavailable" } };
      }
    },
  });
}
