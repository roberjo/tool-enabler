# Getting started

A step-by-step walkthrough from a fresh clone to a project whose AI coding
agent knows how to use your tools. If you just want the command reference,
see the [README](../README.md#cli-reference) instead — this doc is the
slower, narrated version for a first pass.

## 1. Prerequisites

- Python 3.9+
- `git`
- Nothing else — the compiler's only dependency is PyYAML, installed for you
  in step 2.

## 2. Install

```bash
git clone https://github.com/roberjo/tool-enabler.git
cd tool-enabler
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

`pip install -e .` puts a `tool-enabler` command on your PATH (inside the
venv) backed by the checkout you just made — editing a profile and re-running
a command picks up the change immediately, no reinstall needed.

## 3. Look at what's already in the catalog

```bash
tool-enabler list
```

Each row is one **profile** — a YAML file in `profiles/` describing one CLI
tool or API-based system: when to reach for it, the exact commands to run,
how to parse the output, and what to do if it turns out to be missing or
unauthenticated. `[api]` tags a system reachable only over HTTP (Jira, Slack,
Splunk, ...); everything else is a local CLI binary.

```bash
tool-enabler validate
```

Checks every profile in the catalog is well-formed YAML matching the schema.
Run this after editing any profile, before building.

## 4. Pick which tools a project cares about

Not every project needs all 30+ profiles. `init` writes a small manifest —
`.tool-enabler.yaml` — recording which ones this particular project wants:

```bash
mkdir -p /tmp/demo-project
tool-enabler init /tmp/demo-project --tools gh,git,docker
cat /tmp/demo-project/.tool-enabler.yaml
```

This step is optional — `build` compiles the *entire* catalog if no manifest
exists and no `--tools` flag is given — but for a real project you almost
always want a subset, so the agent isn't wading through profiles for tools
that aren't installed here.

## 5. Compile

```bash
tool-enabler build --target /tmp/demo-project
```

This reads `.tool-enabler.yaml` (since we wrote one) and generates:

```
/tmp/demo-project/.claude/skills/gh-cli/SKILL.md
/tmp/demo-project/.claude/skills/git-cli/SKILL.md
/tmp/demo-project/.claude/skills/docker-cli/SKILL.md
/tmp/demo-project/AGENTS.md
/tmp/demo-project/GEMINI.md
/tmp/demo-project/.github/copilot-instructions.md
```

Open `/tmp/demo-project/AGENTS.md` and look for the section between
`<!-- BEGIN TOOL-ENABLER -->` and `<!-- END TOOL-ENABLER -->` — that's the
generated content. Everything outside those markers is left untouched, so
this is safe to run against a project's real, already-populated `AGENTS.md`.

## 6. Re-run it — idempotency

```bash
tool-enabler build --target /tmp/demo-project
```

Run it again with nothing changed and you'll see `Everything already up to
date.` — unchanged output is left alone rather than rewritten, so re-running
`build` in CI or a pre-commit hook doesn't create noisy diffs.

Edit `.tool-enabler.yaml` to add or remove a tool, or edit a profile in
`profiles/`, and re-run `build` — only the files that actually changed are
rewritten.

## 7. Use it in a real project

Point `--target` at an actual repository instead of a scratch directory.
Commit the generated `AGENTS.md`/`GEMINI.md`/`.github/copilot-instructions.md`
and `.claude/skills/` — check the `.tool-enabler.yaml` manifest in too, so a
future `build` (by you or a teammate) reproduces the same output.

## Next steps

- **Have your own custom CLI tool to add?** See
  [docs/custom-tools.md](custom-tools.md) — it walks through scaffolding a
  brand-new profile end to end.
- **Editing an existing profile, or want the full field-by-field schema?**
  See [profiles/README.md](../profiles/README.md).
- **Something not behaving as expected?** See [docs/faq.md](faq.md).
