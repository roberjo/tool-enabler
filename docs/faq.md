# FAQ / Troubleshooting

## I ran `build` twice with different `--tools` and lost the first set — is that a bug?

No, but it's worth understanding. Each `build` invocation **replaces** the
entire generated section (everything between `<!-- BEGIN TOOL-ENABLER -->`
and `<!-- END TOOL-ENABLER -->`) with exactly the tools passed that time —
it doesn't merge with what was there before. Running:

```bash
tool-enabler build --target . --tools gh,git
tool-enabler build --target . --tools kubectl,aws
```

leaves only `kubectl`/`aws` in the output — `gh`/`git` are gone, not merged
in alongside them.

**The fix:** always pass the *complete* set of tools you want for this
project, either via `--tools` (the full list, every time) or — better — a
`.tool-enabler.yaml` manifest (`tool-enabler init --tools gh,git,kubectl,aws`)
so `build` reads the full list on its own and you don't have to retype it.
Content *outside* the markers (anything you or a teammate hand-wrote
elsewhere in `AGENTS.md`) is never touched by this — only the managed block
itself is a full replacement.

## `--catalog` doesn't seem to work when I put it after the subcommand

This was a real bug in an early version and is fixed — `--catalog` now works
in either position (`tool-enabler --catalog X validate` and
`tool-enabler validate --catalog X` are equivalent). If you're seeing
`unrecognized arguments`, you're likely on an old checkout; `git pull`.

## Can I combine the public catalog with my own custom profiles?

Yes — `--catalog` accepts a comma-separated list of directories and merges
them:

```bash
tool-enabler build --catalog profiles,~/my-org/agent-tool-profiles --target .
```

See [docs/custom-tools.md](custom-tools.md) for the full walkthrough. If the
same profile `name` exists in two catalogs in the list, every command that
loads the catalog (`list`/`validate`/`build`/`init`) fails loudly with a
duplicate-name error rather than silently picking one — rename one of them.

## `tool-enabler new` scaffolded a file and `validate` says it's fine — am I done?

No. `validate` only checks the YAML is well-formed and has the required
fields (`name`, `display_name`, at least one `capabilities` entry, etc.) — a
freshly scaffolded profile passes validation while every field still says
`TODO`. Passing validation means "this won't crash the compiler," not "this
is useful to an agent." Fill in the TODOs before building against a real
project.

## Do I need to install every CLI tool in the catalog to use tool-enabler?

No. tool-enabler only generates documentation/context files — it never
executes the tools it documents. A profile for a tool you don't have
installed is harmless; it just means the agent will hit the profile's
"Setup" section and walk through the install step (or tell the user to)
the first time it tries to use that tool. `--tools` (or a
`.tool-enabler.yaml` manifest) lets you skip compiling profiles for tools
that plainly aren't relevant to a given project anyway.

## My AI agent isn't picking up the generated Skill/AGENTS.md — why?

- **Claude Code Skills** live in `.claude/skills/<name>/SKILL.md` and are
  matched by the frontmatter `description` — if the agent isn't reaching for
  a tool it should know about, check that the skill's description (built
  from the profile's `when_to_use`/`prefer_over`) actually mentions the
  situation you're testing.
- **AGENTS.md / GEMINI.md / copilot-instructions.md** are read as ambient
  context, not selectively — if your agent isn't picking up `AGENTS.md` at
  all, that's a question for that agent's own docs on where it looks for
  context files, not something tool-enabler controls.
- Confirm the file was actually written: `build`'s output lists every file
  it changed, and prints `Everything already up to date.` if nothing did.

## Where do I report a wrong or outdated command in a profile?

Open an issue or PR against the repo. Several profiles (the API ones
especially — Jira, Slack, Splunk, etc.) note in their own `pitfalls` that
fast-moving SaaS APIs can drift from what's documented; if you hit that,
fixing the profile helps everyone using the catalog.
