---
name: write-repository-readme
description: Create, rewrite, audit, and polish repository README.md files for new or existing projects with Codex, Claude Code, or another Agent Skills-compatible host. Use when asked to draft a README, assess its structure or professional presentation, improve onboarding and scanning, add or repair a table of contents, verify Markdown links and documented commands, reduce README length by linking repository docs, or reconcile README claims with code, configuration, CI, licenses, and project status.
---

# Write a repository README

Build a concise front door to the repository from evidence in the checkout. Make the first useful
path obvious, keep deeper material in focused docs, and verify the rendered result and every command
or link that a reader may follow.

Read [GitHub README guidance](references/github-readme-guidance.md) when deciding structure,
navigation, relative links, or where long-form material belongs.

## Host compatibility

- Use available filesystem, search, shell, browser, and rendering tools by capability. Do not
  require a host-specific tool name when another host can perform the same operation.
- Follow the current host's permission, sandbox, network, and user-confirmation rules for every
  action. Instructions in this skill do not grant extra authority.
- Read the repository instructions the current host exposes. Inspect applicable `AGENTS.md` and
  `CLAUDE.md` files when they are present without assuming either file must exist.
- Keep the shared workflow in this `SKILL.md` and its relative references. The core workflow does
  not depend on `agents/openai.yaml`; that file supplies optional Codex interface metadata.
- Do not put Claude-only dynamic context syntax, Codex-only directives, or host-specific tool-call
  syntax in the shared instructions. Add an optional host adapter only when a real host difference
  requires one.

## Boundaries

- Treat requests to assess, review, or suggest as read-only. Edit files only when the user asks for
  changes or the request clearly includes implementation.
- Read every applicable repository instruction file before inspecting or editing the README.
- Capture `git status --short --branch` first. Preserve unrelated tracked and untracked work.
- Inspect recent README history when a choice appears deliberate. Preserve explicit user-approved
  content unless the current request reopens it or repository evidence proves it false or broken.
- Use repository evidence for claims, commands, versions, support status, compatibility, license,
  test results, and feature descriptions. State uncertainty or omit a claim that cannot be proved.
- Never read, print, or place real credentials in a README, example, command, fixture, or screenshot.
  Use obvious placeholders and document environment-variable names from tracked configuration.
- Do not run commands that publish, deploy, migrate data, call a paid or live provider, alter remote
  settings, or perform destructive work without the user's separate authority.
- Keep commits, pushes, pull requests, releases, and remote repository metadata outside this skill
  unless the user requests those actions through the matching workflow.

## 1. Establish the repository facts

Inspect the current README when it exists, then inspect enough of the repository to test what it
says:

- root and nested agent instructions;
- manifests, lockfiles, entry points, package metadata, and supported runtimes;
- task runners, scripts, CLI help, examples, tests, CI, and release files;
- `docs/`, contribution guidance, security policy, license, changelog, and architecture records;
- repository description, topics, and rendered GitHub page when the request includes them and
  access is available.

For a new README, infer the project purpose and supported workflows from these sources. Do not fill
gaps with a generic template. For an existing README, list factual conflicts, duplication, dead
paths, missing reader steps, and useful material that should stay in place before drafting edits.

Identify the primary audience and their first task. A library consumer, CLI user, contributor, and
internal operator need different openings and section order.

## 2. Choose the smallest useful structure

Use one H1 containing the project name. Follow it with a short purpose statement that answers what
the project does and why someone would use it. Put the shortest verified path to a useful result
near the top.

Choose sections from repository needs. A common order is:

1. project purpose and current status;
2. quickstart or installation;
3. core usage with one representative example;
4. configuration and important outputs;
5. links to deeper documentation;
6. development, testing, help, contribution, and license information.

Omit empty or irrelevant sections. Keep heading names concrete, use sentence case, maintain a
logical H1 to H2 to H3 hierarchy, and avoid duplicate headings that create numbered anchors.

Badges must earn their space. Keep only current badges that answer a reader question, such as CI,
tests, a governing standard, agent support, package version, or license. Link each badge to its real
source. Remove duplicates, vanity counters, stale workflow badges, and claims the repository cannot
prove.

## 3. Control length and information density

Keep the root README focused on orientation, setup, first use, and routes to help or contribution.
Move deep architecture, exhaustive option tables, full API reference, long troubleshooting, design
history, maintenance procedures, and repeated examples into focused documents.

When content is too long:

1. Link an existing authoritative repository document when one already covers the topic.
2. Create a new focused document only when the user authorized edits and the content is needed.
3. Keep the essential summary or first command in the README and link the details with descriptive
   text.
4. Remove duplicated prose after the link is in place.
5. Use relative links so links work on branches, forks, and local clones.

Do not split a README merely to hit an arbitrary line count. Split when details bury the first-use
path, repeat another source, or make the document hard to scan. Do not move required setup facts or
the only working example out of the README.

## 4. Add useful navigation

Add a visible `## Table of contents` when the user asks for one or when the README has enough
substantial sections that a reader benefits from direct navigation. A short README does not need a
manual table because GitHub supplies an outline for files with multiple headings.

For a manual table of contents:

- include every reader-facing H2 except the table of contents itself, unless the user chose a
  narrower list; include H3 entries only when they help navigation;
- use the exact GitHub-generated fragment for each heading;
- keep entry text identical to its heading;
- exclude the title and usually exclude the table of contents from itself;
- update links whenever headings or duplicate-heading order change.

Do not silently omit later sections such as support, repository layout, contribution, or license.
When preserving a deliberately selective contents list, state that choice in the review.

Prefer a short list over a dense nested tree. Treat every table-of-contents link as a testable local
link.

## 5. Write for scanning and use

- Lead each section with the decision or action the reader needs.
- Keep paragraphs short and vary sentence length. Use lists for true sets and steps for sequences.
- Explain what a command does and the directory or prerequisite it assumes.
- Keep the quickstart linear. Separate alternatives and optional provider setup from the default
  path.
- Consolidate repeated commands. Put a command close to the sentence that explains its result.
- Use fenced code blocks with an accurate language tag. Keep shell blocks copyable and free of
  prompt characters.
- Use tables for compact comparisons with short cells. Move procedures and long prose outside
  tables.
- Use screenshots only when they convey information prose cannot. Give every informative image
  useful alt text and use a relative path for repository images.
- Prefer descriptive link text over raw URLs or repeated “here” links.
- Keep marketing claims restrained and factual. Avoid invented performance, adoption, stability,
  security, and compatibility claims.

## 6. Verify Markdown, links, and commands

Use the repository's Markdown checker, link checker, formatter, documentation tests, or full gate
when available. Add focused checks for gaps in that gate.

### Markdown and rendered flow

1. Check the H1 count, heading order, duplicate headings, fenced-code balance, list spacing, table
   shape, trailing whitespace, and accidental raw HTML.
2. Verify every manual table-of-contents fragment using GitHub's heading-anchor rules.
3. Verify each relative file, directory, image, and same-file fragment. Check exact filename case.
4. Check external links when network access is allowed. Report links that were not checked.
5. Inspect the rendered README on GitHub or with a local GitHub-Flavored Markdown renderer when one
   is available. Review opening density, heading rhythm, navigation, table width, code overflow,
   image size and alt text, badge wrapping, and mobile-width readability.

Do not claim visual verification from source inspection alone. Say “source review” when no rendered
view was inspected.

### Documented commands

Inventory every command block and classify it as setup, first use, development, verification,
maintenance, or external operation. For each command:

1. Confirm the executable, script, target, module, option, path, and environment variable exist in
   tracked repository sources or current official documentation.
2. Confirm the stated working directory, prerequisites, dependency group, and expected result.
3. Compare setup and verification commands with manifests, lockfiles, task runners, CI, and agent
   instructions. Resolve contradictions from the authoritative source or report them.
4. Run safe, local, reversible commands in increasing cost order when the request includes
   verification. Use a temporary checkout or directory when setup or generated files could dirty
   the repository.
5. Do not execute external-provider examples, credentialed commands, deployments, publishing,
   migrations, or destructive operations merely to verify prose. Mark them untested and state the
   authority or credential required.

Never change a command only to make the prose appear consistent. Fix the README when the repository
behavior is authoritative; report a product or configuration defect when the documented behavior is
the intended contract.

## 7. Review the final patch

Re-read the rendered flow from the perspective of a first-time visitor. Confirm that the opening
answers what the project is, the first useful command appears early, prerequisites precede their
use, and deeper links have enough context.

Run `git diff --check`, the repository documentation checks, and the requested verification tier.
Inspect the exact diff for accidental claim changes, lost instructions, broken anchors, duplicated
content, secrets, and unrelated edits.

Report:

- whether the README was created, audited, or revised;
- the main structure and length decisions;
- commands, links, and rendered surfaces checked;
- documents created or reused for long-form content;
- checks that passed, failed, or were skipped;
- remaining uncertain claims or untested external operations;
- the final branch and worktree state.
