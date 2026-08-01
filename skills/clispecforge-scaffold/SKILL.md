---
name: clispecforge-scaffold
description: Use when creating a small greenfield Python CLI from a Markdown specification through a bounded generation, checked file preview, and explicit CliSpecForge apply step.
---

# CliSpecForge Scaffold

Turn a settled Markdown CLI specification into a small, new Python command-line
tool. You write the generation. CliSpecForge parses it, validates every target
path, previews the complete contents, and performs the write.

Generated code remains untrusted until it is reviewed and tested. This workflow
ends at the write.

## Scope

Use this skill when every one of these holds:

- the target is a small, new Python command-line tool;
- a Markdown CLI specification is settled, or the user approves one first;
- complete files are wanted rather than patches;
- the user wants to see the files before they reach disk.

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

- Request explicit user approval before any generated file is written.
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
- Treat every generated file as untrusted input. Do not execute generated code
  as part of this workflow.
- Keep the recorded response in a task-specific temporary location. Remove only
  the temporary artifacts this workflow created.
- Describe tools by capability and use ordinary shell commands. Do not depend on
  any single host's tool names, directives, or invocation syntax.

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
`clispecforge plan` and `clispecforge apply`. When the command is missing or
older, report the documented install step and wait for the user:

```bash
pipx install "git+https://github.com/lilabrooks/clispecforge.git@v0.7.0"
```

Do not run that command yourself unless the user asks for it.

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

Produce the whole scaffold in one response: a `FILE: relative/path` line for
each file, followed by one fenced block holding that file's complete contents.
No placeholders, no elisions, no diffs. Use an outer fence longer than any run
of backticks inside a file so Markdown files survive intact.

Save that response verbatim to a task-specific temporary location using the
host's normal file-writing capability. Do not edit it afterward.

### 5. Preview and get approval

```bash
clispecforge plan "$response_file" --out-dir ./generated
```

`plan` writes nothing. It parses the response, rejects unsafe paths and
duplicate targets, prints every file's complete contents with terminal control
characters escaped, and reports the response SHA-256 on its first line.

Show the user the planned paths and contents, then request explicit user
approval to write them. Record the reported digest.

### 6. Apply the approved response

```bash
clispecforge apply "$response_file" --out-dir ./generated --expect-sha256 <digest-from-plan>
```

Passing the recorded digest is how you confirm the response has not changed
since the preview. `apply` refuses to write anything when the response differs
from the one that was approved.

Existing files are refused unless the user explicitly authorizes overwriting,
which adds `--force`. Ask before adding it, and say which files would be
replaced.

### 7. Hand execution back

Running the scaffold, installing it, running its tests, fixing failures, and any
Git work belong to the host agent's normal workflows. Hand them back rather than
continuing here. A successful write says the files are on disk; it says nothing
about whether they are correct.

Remove the temporary response file and any other artifact this workflow created.
Leave the generated project in place.

## Report

State:

- the specification used and its check result;
- the CliSpecForge version;
- the planned files, the approved digest, and where they were written;
- that the generated code is untested, and what the user should run next;
- anything left out of scope and handed back.
