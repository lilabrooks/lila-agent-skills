---
name: clispecforge-scaffold
description: Create a small greenfield Python CLI from a settled Markdown specification with CliSpecForge's offline plan/apply handoff. Use in Codex or Claude Code when the user wants complete project files previewed and explicitly approved before they are written. Do not use for existing-repository changes, test-and-repair loops, Git work, or large systems.
---

# CliSpecForge Scaffold

Turn a settled Markdown CLI specification into a small, new Python command-line
tool. You write the generation. CliSpecForge parses it, validates every target
path, previews the complete contents, and performs the write.

Generated code remains untrusted until it is reviewed and tested. This workflow
ends at the write.

## Host compatibility

- Follow the active host's permission, sandbox, network, and confirmation rules.
  This skill grants no additional authority.
- Use the host's filesystem, shell, temporary-file, and user-confirmation
  capabilities. Do not depend on any single host's tool names, directives, or invocation syntax.
- The core workflow does not depend on `agents/openai.yaml`; that file supplies
  optional Codex presentation only. Keep the shared workflow in this `SKILL.md`.
- In a non-interactive task, stop after the plan and report the response path,
  digest, destination, and complete preview. Resume the apply only in a later
  interactive turn with the user's explicit approval.

## Scope

Use this skill when every one of these holds:

- the target is a small, new Python command-line tool;
- a Markdown CLI specification is settled, or the user approves one first;
- complete files are wanted rather than patches;
- the user wants to see the complete proposed project files before they are
  written to the destination.

Route this work to the host agent's normal repository workflow instead:

- refactors or changes inside an existing repository;
- patch-based or diff-based edits;
- autonomous build, test, and repair loops;
- Git operations, including branching, committing, and pull requests;
- large or multi-package systems.

Confirm the request fits this scope before running anything. When part of the
request is outside this skill's scope, say which part and hand it to the host
agent's normal repository workflow rather than stretching this workflow to
cover it.

## Rules

- Request explicit user approval after a successful plan and before any proposed
  project file is written. A build request or approved specification does not
  authorize the apply.
- Never install CliSpecForge, a provider SDK, or any other package
  automatically. Report the missing command and the documented install step,
  then stop and wait.
- Never read, set, or modify provider credentials, and never configure a model
  provider. This workflow sends no request through CliSpecForge, so no
  credential is needed at any step.
- Validate the specification before generating. Do not generate against a
  specification that still fails `clispecforge spec check`.
- Apply the exact response that was previewed and approved. Prove it with the
  digest rather than assuming the file is unchanged.
- Do not modify the recorded response after planning it. If it changes for any
  reason, run `plan` again and request fresh approval.
- Treat every generated file as untrusted input. Do not execute generated code
  as part of this workflow.
- Keep the recorded response in a task-specific temporary location. Remove only
  the temporary artifacts this workflow created.

## Workflow

### 1. Confirm scope and the specification

1. Check the request against the scope above. Stop here when it does not fit.
2. Create or select a Markdown CLI specification. A specification has `Purpose`,
   `Commands`, `Inputs`, `Outputs`, `Behavior`, and `Acceptance tests` sections.
   Get the user's approval on a specification you drafted before generating from
   it.

### 2. Check the engine

Confirm the command exists and is new enough:

```bash
clispecforge --version
```

This workflow needs CliSpecForge 0.7.0 or newer, which is the first version with
`clispecforge plan` and `clispecforge apply`. Compare the reported semantic
version, not its text lexicographically.

When the command is missing or older, report that Python 3.12 or newer and
`pipx` are prerequisites, give this audited commit-pinned install step, and wait
for the user:

```bash
pipx install "git+https://github.com/lilabrooks/clispecforge.git@fb3e0c873c5662b91d44d484cae74e01b630d819"
```

That commit reports version 0.7.0 and contains the offline `plan` and `apply`
commands. It is pinned because a `v0.7.0` tag did not exist when this workflow
was verified. Do not substitute an unpinned branch. Do not run the install
command unless the user separately asks for installation.

### 3. Validate the specification

```bash
clispecforge spec check path/to/spec.md
```

Resolve every reported error before generating. A specification that fails this
check is not ready to build against.

### 4. Generate complete files

Read the file-output contract and follow it exactly:

```bash
clispecforge skill show file-output-contract
```

Stop and report an incomplete or unsupported CliSpecForge installation if this
command fails. Do not reconstruct a missing contract from memory.

Produce the whole scaffold in one response: a `FILE: relative/path` line for
each file, followed by one fenced block holding that file's complete contents.
No placeholders, no elisions, no diffs. Use an outer fence longer than any run
of backticks inside a file so Markdown files survive intact.

Choose an explicit destination directory. If the user did not name one, use
`./generated` as the proposed destination and include it in the approval
request.

Save the response verbatim as UTF-8 in a task-specific temporary directory using
the host's normal file-writing capability. Creating this recorded response is a
preparation step; it does not write the proposed files into the destination. Do
not edit the response after saving it.

### 5. Preview and get approval

```bash
clispecforge plan "$response_file" --out-dir "$out_dir"
```

`plan` writes nothing. It parses the response, rejects unsafe paths and
duplicate targets, prints every file's complete contents with terminal control
characters escaped, and reports the response SHA-256 on its first line.

Require a successful exit. Show the user the exact destination, planned paths,
and complete contents, then request explicit user approval to write them. Record
the reported digest. In a non-interactive task, stop here.

Inspect the planned targets before asking. If any target exists, list it and get
separate overwrite approval; approval of the contents alone does not authorize
replacement.

### 6. Apply the approved response

```bash
clispecforge apply "$response_file" --out-dir "$out_dir" --expect-sha256 <digest-from-plan>
```

Passing the recorded digest is how you confirm the response has not changed
since the preview. `apply` refuses to write anything when the response differs
from the one that was approved.

Add `--force` only when the user explicitly approved every existing target that
will be replaced. Do not retry with `--force` after a refusal unless that
approval is already recorded.

Require a successful exit and confirm the command reported the expected writes.
Do not execute, import, install, or test the generated code in this workflow.

### 7. Hand execution back

Running the scaffold, installing it, running its tests, fixing failures, and any
Git work belong to the host agent's normal workflows. Hand them back rather than
continuing here. A successful write says the files are on disk; it says nothing
about whether they are correct.

Remove the temporary response file and any other artifact this workflow created
after success, rejection, or a terminal error. Leave the generated project in
place after a successful apply.

## Report

State:

- the specification used and its check result;
- the CliSpecForge version;
- the planned files, the approved digest, and where they were written;
- that the generated code is untested, and what the user should run next;
- anything left out of scope and handed back.
