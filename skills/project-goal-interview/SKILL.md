---
name: project-goal-interview
description: Conduct a short owner interview that turns a project idea or vague brief into a concrete, testable goal and an ordered first milestone. Use when starting a project, defining or revising its objective, filling goal or mission placeholders, recovering intent in an existing repository, or converting broad direction into target behavior, success checks, constraints, non-goals, and realistic examples.
---

# Project goal interview

Turn the owner's intent into a goal an agent or team can execute and verify. Ask a few questions at
a time, draft as answers arrive, and use the repository's own format when one exists.

## Host compatibility

- Run this skill as `$project-goal-interview` in Codex or `/project-goal-interview` in Claude Code.
- Keep the shared workflow in this `SKILL.md` using the common Agent Skills `name` and
  `description` frontmatter.
- Treat `agents/openai.yaml` as optional Codex interface metadata. The core workflow does not
  depend on `agents/openai.yaml`.
- Use filesystem, search, shell, and conversation tools by capability. Follow the active host's
  permission, sandbox, and user-confirmation rules.
- Keep Claude Code dynamic-context syntax, Claude-only frontmatter, Codex directives, and
  host-specific tool-call syntax out of the shared workflow.

## Boundaries

- Read every applicable repository instruction file before inspecting or editing project files.
- Treat an interview, review, or recommendation request as read-only. Return a draft in the
  conversation unless the user also asked for file changes.
- During read-only work, do not write persistent memory, session notes, scratch files, or other
  host state. Use only inspection commands that leave the workspace and host state unchanged.
- Edit a repository goal artifact only when the user asks. Preserve owner-written content and
  present any proposed replacement for confirmation.
- Keep implementation, dependency changes, publishing, and other follow-on work outside this
  interview unless the user separately requests it.

## Prepare from evidence

1. Locate any goal, product brief, specification index, roadmap, architecture record, README, and
   repository instructions. Follow the local naming and document structure.
2. Capture the worktree state before editing. Preserve unrelated tracked and untracked work.
3. Inspect the codebase before asking questions when implementation already exists. Identify the
   primary interface, current behaviors, test and run commands, supported platforms, and visible
   gaps. Offer these findings as proposed answers for the owner to correct.
4. Separate facts observed in the repository from owner choices and unresolved questions. State
   evidence limits plainly.

## Run the interview

Adapt the sequence to information already known. Ask one or two compact groups at a time and show
the draft taking shape.

1. **Purpose and audience.** Ask what is being built, who will use it, and which concrete problem
   it should solve. Identify the deliverable type in the owner's own terms.
2. **Target state.** Ask what exists and works when the project is complete. Name interfaces,
   artifacts, behaviors, and boundaries instead of broad directions such as "modernize the API."
3. **Representative interactions.** Gather 2 to 4 realistic examples through the primary
   interface, including one realistic edge or malformed input. Capture the input, expected output
   or state change, and expected error behavior.
4. **Proof.** Ask for observable success checks and real verification commands. Confirm commands
   against the repository when possible. For a new project, record commands that the first
   milestone must establish. Mark checks that need unavailable equipment, accounts, services, or
   owner judgment as owner-gated.
5. **Scope edges.** Ask which adjacent capabilities belong outside this goal. Write non-goals
   narrowly enough to settle later scope questions.
6. **Constraints and open choices.** Record fixed runtime, platform, compatibility, policy,
   dependency, schedule, and budget constraints. Keep undecided design choices visibly open and
   follow any decision process the repository already defines.
7. **First shippable slice.** Find the smallest coherent outcome that moves the target state
   forward and can be checked on its own. Give it an observable completion condition.

Push until every success claim has an observable check. When an answer depends on several files or
systems, trace one representative interaction through input, handoff, consumer, output, and
verification. Ask for clarification when two answers conflict or when a missing choice would change
the project's direction.

## Draft the goal

Follow the repository's current goal format. When none exists and the user requested a file, use a
small Markdown document with these sections:

- purpose, audience, and problem;
- concrete deliverable and target state;
- representative interactions and expected results;
- success criteria with verification commands;
- non-goals;
- fixed constraints and open decisions;
- ordered milestones, starting with the first shippable slice.

Write each milestone as an outcome plus its verification. Derive later milestones from the stated
target instead of inventing optional scope. Include onboarding or quickstart verification when the
finished deliverable is meant for another person to install or use.

Before confirmation, inventory every behavior assigned to the first slice. Keep behaviors required
for its core path, safety, or an explicit owner constraint. Move other behaviors later. When an
owner constraint makes the slice larger, name that tradeoff instead of quietly packing it in.

Keep the goal concise enough to reread during ordinary work. Move detailed contracts into the
repository's existing specification system and link them from the goal when needed.

## Confirm and hand off

Check the completed draft against every interview answer. Call out unresolved choices, owner-gated
checks, and repository evidence that disagrees with the requested target.

Confirm the finished goal with the user before treating it as authoritative or beginning project
work. End after the confirmed draft or requested goal-file update, and report the files changed and
checks run.
