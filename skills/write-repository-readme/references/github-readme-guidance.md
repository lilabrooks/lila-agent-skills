# GitHub README guidance

Use these primary sources when a README decision depends on GitHub rendering or repository
conventions. Check the live pages when current behavior matters.

## Repository README content

[About the repository README file](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
states that a README commonly explains what a project does, why it is useful, how to get started,
where to get help, and who maintains or contributes to it. GitHub says the README should contain the
information needed to start using and contributing to the project, with longer material placed in
long-form documentation. GitHub truncates rendered README content beyond 500 KiB; treat that as a
platform limit, not a sensible target length.

Practical rule: keep orientation, first use, and routes to help in the root README. Link existing
repository docs for deep material. Create a focused local document when the content is necessary,
the user authorized edits, and no current document owns it. A local `docs/` file travels with clones
and branches; a project may use a wiki when that is its chosen documentation source.

[Best practices for repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/best-practices-for-repositories)
recommends a README for each repository so visitors can understand and navigate the work.

## Headings, navigation, and links

[Basic writing and formatting syntax](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)
documents these GitHub behaviors:

- Heading levels create document hierarchy.
- GitHub supplies an outline for Markdown files with 2 or more headings.
- Heading fragments lowercase letters, replace spaces with hyphens, remove most punctuation and
  markup, and add numeric suffixes to duplicate fragments.
- Relative links follow the current branch and work in a local clone. GitHub recommends them for
  other files in the same repository.
- Markdown link text must remain on one source line.
- Informative images need a short text equivalent in their alt text; repository images should use
  relative paths.

Practical rule: use a visible table of contents for a substantial README or when the user asks for
one. GitHub's outline makes a manual table unnecessary in a short file. Test manual fragments after
every heading edit.

## GitHub-Flavored Markdown

The [GitHub-Flavored Markdown specification](https://github.github.com/gfm/) defines the syntax
GitHub renders. It covers heading blocks, paragraphs, fenced code, links, and the GFM table
extension. Table cells accept inline content, not block-level procedures or code blocks.

Practical rule: use fenced code blocks for commands and examples. Reserve tables for short,
parallel facts that readers compare by row.

## Contribution and support files

[Setting guidelines for repository contributors](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors)
documents GitHub's special handling for `CONTRIBUTING.md` in a repository root, `docs/`, or
`.github/`. Link that file from the README instead of duplicating a long contribution procedure.

Apply the same ownership rule to a code of conduct, security policy, citation file, license,
changelog, architecture record, and full reference guide: summarize what a first-time reader needs,
then link the authoritative file.
