---
name: architecture-decision-interview
description: Conduct a structured interview for a consequential architecture choice and produce or revise an architecture decision record using the repository's conventions. Use when choosing a dependency, persistence model, service or ownership boundary, security or privacy approach, public contract, deployment shape, or another costly or hard-to-reverse design; also use when an ADR draft lacks evidence, credible alternatives, consequences, or a rollback condition.
---

# Architecture decision interview

Frame one decision, compare credible options against checked evidence, and record the chosen course
in the repository's existing ADR format.

## Host compatibility

- Run this skill as `$architecture-decision-interview` in Codex or
  `/architecture-decision-interview` in Claude Code.
- Keep the shared workflow in this `SKILL.md` using the common Agent Skills `name` and
  `description` frontmatter.
- Treat `agents/openai.yaml` as optional Codex interface metadata. The core workflow does not
  depend on `agents/openai.yaml`.
- Use filesystem, search, shell, web, and conversation tools by capability. Follow the active
  host's permission, sandbox, network, and user-confirmation rules.
- Keep Claude Code dynamic-context syntax, Claude-only frontmatter, Codex directives, and
  host-specific tool-call syntax out of the shared workflow.

## Boundaries

- Read every applicable repository instruction file before inspecting or editing project files.
- Treat an interview, review, or recommendation request as read-only. Return a draft in the
  conversation unless the user also asked for an ADR file change.
- During read-only work, do not write persistent memory, session notes, scratch files, or other
  host state. Use only inspection commands that leave the workspace and host state unchanged.
- Keep implementation outside this skill. A request to interview, recommend, or write an ADR does
  not authorize code changes, dependency installation, migration, deployment, or publishing.
- Never mark an ADR accepted, supersede an accepted decision, or reverse work without the authority
  required by the repository and the user.

## Establish the decision boundary

1. Capture the worktree state and locate repository instructions, architecture records,
   specifications, dependency manifests, and code involved in the choice.
2. Read accepted decisions and governing contracts before framing a new one. Surface any conflict
   that would require an accepted decision to be superseded.
3. Confirm that the choice affects a durable boundary, external contract, costly dependency,
   operational model, security posture, stored data, or another hard-to-reverse part of the system.
   Handle local implementation choices through the repository's normal workflow.
4. State the exact decision to make, why it must be made now, who owns it, and which implementation
   work remains outside the interview.

## Run the interview

Ask a few questions at a time. Reuse facts already present in the repository and invite the owner
to correct them.

1. **Trigger and desired outcome.** What changed or became possible? Which project goal, failure,
   constraint, or opportunity forces this choice?
2. **Scope and invariants.** Which users, components, data, contracts, and operating environments
   are affected? Which properties must remain true?
3. **Current mechanism.** How does the system behave today? Trace one representative outcome from
   producer through handoff and consumer to its verification.
4. **Candidate options.** Gather the owner's preferred option, credible alternatives, and the
   current course when it is viable. Describe each option concretely enough to test its mechanism.
5. **Decision drivers.** Rank the constraints that can separate the options. Use measured limits,
   named policies, compatibility requirements, operational burden, cost, schedule, security, and
   reversibility where they genuinely apply.
6. **Evidence and uncertainty.** Match each mechanism claim to repository evidence, a current
   primary source, or a clearly labeled assumption. State which mechanism claims were checked and
   which remain uncertain.
7. **Failure semantics.** Trace a representative mid-operation failure. Decide whether work stops,
   retries, or continues; what partial output survives; how incomplete results are labeled; and
   which observable status, error, or exit behavior prevents them from looking complete.
8. **Consequences and exit.** Ask what each option makes easier or harder and which files or systems
   must change together. Record migration and rollback separately from the observable conditions
   that should reopen the decision.

Preserve quiet real-world samples as evidence of the base rate. Avoid extending a sample merely to
obtain a preferred result. Flag any experiment, instrumentation, or validation step that changes
the operating configuration being compared.

For costly or hard-to-reverse choices, seek an independent review when a suitable reviewer is
available. Keep the review effort proportionate to the expected cost and blast radius.

## Compare and recommend

Use the decision drivers to compare every credible option. For each option, record:

- the mechanism and affected boundaries;
- evidence checked and important unknowns;
- expected benefits and costs;
- security, privacy, operational, compatibility, and maintenance effects that apply;
- failure containment and partial-result semantics;
- migration and rollback;
- the observable trigger for reconsideration.

State a recommendation when the user asked for one. Explain why it wins against the ranked drivers
and how uncertainty could change the result. Leave the choice with the named decider when repository
policy or the user reserves it.

## Write the ADR

Follow the repository's existing location, numbering, frontmatter, status vocabulary, index, and
linking conventions. Preserve relevant material in an existing draft and show substantive changes
for confirmation.

When the repository has no ADR convention and the user requested a file, write a concise Markdown
record with:

1. title and proposed status;
2. context and decision trigger;
3. decision drivers and fixed constraints;
4. options considered with checked evidence;
5. decision and scope;
6. consequences and required follow-up;
7. failure semantics and containment;
8. verification plan;
9. migration and rollback;
10. revisit conditions.

Choosing an option during the interview leaves the ADR Proposed. Reserve `Accepted` for an explicit
acceptance statement from the authorized decider. Before that statement, describe the selected
option as proposed or chosen without labeling the decision accepted. Name unsupported claims and
unresolved questions in the record rather than sanding them into certainty.

## Confirm and finish

Read the draft back against the interview. Confirm that alternatives are credible, consequences
cover every affected boundary, failure semantics are complete, and rollback and reconsideration
conditions are separately observable. Ask the authorized decider directly whether the draft is
confirmed. A revision request or withheld acceptance leaves its status Proposed.

End after the requested ADR draft or file update. Report the evidence checked, remaining
uncertainties, files changed, and validation performed. Wait for separate authority before starting
implementation or changing the ADR's acceptance state.
