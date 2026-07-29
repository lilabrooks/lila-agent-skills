---
name: record-project-memory
description: Capture a repository's existing project knowledge as owner-approved goal, specification, and decision-record files that future agent tasks can find and use. Use when an agent plans, applies, or reviews durable project memory for a target repository - adding or reconciling project memory, recording an implemented contract as a specification, documenting an already-made decision as an ADR, or assessing what project memory a repository is missing. Record only what repository evidence and owner confirmation already establish, follow the target's existing document conventions and checks, and hand instruction-file and host-configuration work to prepare-agent-compatible-repository.
---

# Record Project Memory

Give a repository the smallest set of durable, target-owned memory files that its own evidence
supports, so a later agent task loads the goal, contract, or decision it needs instead of rederiving
it. Every file is generated from that repository's facts and becomes ordinary project content.

## Boundaries

- Record what the repository already establishes. Do not draft a specification for intended behavior
  or an ADR for a decision that has not been made.
- Treat an assessment or planning request as read-only. Report the file plan without writing files.
- Propose files; the owner disposes. Apply only owner-approved files.
- Write nothing outside the target repository. Preserve unrelated work, existing project truth,
  credentials, generated state, and files the request did not name.
- Create no executable, map format, checker, runner, hook, ledger, installable template, site,
  updater, version stamp, manifest, or routine log. This skill writes documents only.
- Add no tool version, provenance digest, or upgrade relationship to an approved file. Once
  accepted, a file is ordinary target-owned content with no tie back to this skill.
- Hand instruction and host-configuration changes to the `prepare-agent-compatible-repository`
  skill. That skill owns `AGENTS.md`, `CLAUDE.md`, nested instruction scope, and host settings.

## 1. Inspect the target

Read before proposing anything:

1. The README, contribution guide, and any existing goal, specification, decision record, or design
   note, wherever the repository keeps them.
2. Manifests, lockfiles, and configuration that show dependency, runtime, and packaging choices.
3. Public interfaces: entry points, exported functions, commands, routes, and schemas.
4. Tests, fixtures, and golden files, which show which behaviors are already pinned.
5. The repository's own verification commands, and the CI that runs them.
6. Existing agent instruction files as context only, plus the Git history behind the areas above.

Record which files already carry project truth. Preserve an existing file that already covers the
need. Create a goal, specification, or decision record only when no suitable target-owned artifact
exists. Rewriting adequate existing documentation is not adoption.

## 2. Choose the smallest useful memory set

Prefer fewer files. Each proposed file must name the future task it would change and the evidence
that supports it. Drop any candidate that only restates the README, only restates obvious source
code, or only repeats generic agent guidance the host already provides.

When repository evidence and owner input support no durable target-specific memory, propose no file
and report the missing evidence. An empty result is a valid outcome; padding a thin repository with
speculative documents is not.

## 3. Draft a goal from repository evidence

Draft the candidate from the repository first, name the evidence paths behind each part, then ask
the owner only about gaps, contradictions, and choices the repository cannot establish. Cover:

- **Goal:** what the repository delivers, for whom, and why.
- **Target state:** the concrete outcomes that define success.
- **Success criteria:** observable behavior and the repository's existing verification commands.
- **Non-goals:** what it deliberately does not do.
- **Constraints:** fixed runtime, dependency, platform, and interface limits.

An intended future outcome enters the goal only after the owner confirms it. A recorded goal is a
durable scope record, not a milestone backlog, task queue, or autonomous iteration policy. Leave
execution, iteration, and completion tracking to ordinary agent guidance and host features.

## 4. Draft specifications and decision records from what exists

A **specification** records implemented behavior supported by a direct test or a reproducible
observation, and confirmed by the owner as an intended contract. A passing repository check alone
does not establish that a contract is intended: it shows the code is healthy today, not that the
behavior is promised. Cite the test or observation for each clause.

A **decision record** captures a decision already made, and only when code, configuration, history,
existing documents, or owner input establishes both the decision and enough of its rationale to
state it honestly. Do not invent historical rationale, rejected alternatives, or consequences. Where
the evidence shows the choice but not the reasoning, either ask the owner or leave the section out
and say why. A dependency proves that the project uses something; it never proves why it won.

Where an existing document already carries the rationale, cite it and reject a duplicate record.

## 5. Follow the target's conventions

Follow the target's existing paths, naming, metadata, sections, indexes, and validators. Match what
the repository already does even when another shape looks tidier, and keep any field its own checks
require.

When the target has no convention, use this fallback and nothing more:

- **Goal:** the 5 sections in step 3.
- **Specification:** `type`, `title`, `status`, `owner`, and an ISO 8601 `date`, then Purpose,
  Contract, and Verification.
- **Decision record:** `type`, `title`, `status`, `owner`, and an ISO 8601 `date`, then Context,
  Decision, Consequences, and Revisit trigger.

Mark a specification `status: current` only after the owner confirms the contract is intended, and
mark a decision record `status: accepted` only after the owner confirms the decision binds future
work. Do not add an index, map, version field, provenance field, or numbering scheme.

## 6. Present the file plan

Before writing, present one plan listing, for each proposed file:

1. The exact path.
2. The evidence behind it, by path.
3. The proposed content and status.
4. The target checks that will run after it lands.
5. Its instruction route: the exact path and read trigger a future agent needs in the applicable
   `AGENTS.md` to find the file when it matters.

Every accepted memory file outside the loaded instruction chain needs that route, or the file is
written but never read. Name the route in the plan even though another skill applies it. Keep full
memory files on disk until their trigger applies, and do not put Claude-style `@` imports in
`AGENTS.md`. A goal file may route to the relevant specifications and decision records.

## 7. Apply, route, and verify

Treat each memory file and its instruction route as one approval unit. Do not write a file whose
route is unresolved: before writing, either confirm that the applicable `AGENTS.md` already carries
the exact route, or obtain the owner's approval for the route change that adds it.

1. Apply only the files the owner approved, generating each from target facts rather than copying a
   canonical template.
2. Resolve each route. When the exact route already exists, record it and continue. When a route
   change is required, hand it to the `prepare-agent-compatible-repository` skill, which applies or
   reconciles the concise instruction and keeps `CLAUDE.md` importing the applicable `AGENTS.md`.
   Do not duplicate that procedure here.
3. Run the target's applicable checks. Limit repairs to the approved paths, and when a check reveals
   a required edit outside them, stop and request approval instead of widening the change.
4. Confirm by rereading the instruction chain that each accepted file is reachable from a loaded
   instruction or an explicit task trigger.

When a route change is required and the `prepare-agent-compatible-repository` skill is unavailable,
stop and report a routing blocker before writing. An accepted file that no loaded instruction
reaches is an unfinished adoption.

When an applicable check cannot start or finish, report the exact command and the blocker.
Without owner approval, never substitute an undocumented command, install dependencies, change
configuration, or widen the approved paths. Never claim verification passed unless the documented
check completed successfully.
Leave the approved changes visible and report verification as incomplete.

Report the files inspected, proposed, accepted, and rejected; the evidence behind each accepted
file; the routes handed off; the checks run and their results; and any need the evidence could not
support. State plainly when the outcome was that no durable memory was warranted.
