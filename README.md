# tool-enabler

A single catalog of "how to use this tool" knowledge, compiled into the
native context format each GenAI coding agent actually reads — Claude Code
Skills, `AGENTS.md`, `GEMINI.md`, and `.github/copilot-instructions.md`.

Covers two kinds of tool: local **CLIs** (`gh`, `git`, `kubectl`, `aws`) and
systems reachable only over **HTTP APIs** (Jira, Confluence, Slack, MS Teams,
Splunk, Jenkins, Harness, qTest). Both are documented the same way — see
"Architecture" below.

## Why

Agents like Claude Code, Copilot, Gemini CLI, and Codex CLI can already run
`gh`, `kubectl`, `aws`, `git`, or a `curl` call via their shell tool — the gap
isn't *execution*, it's *judgment*: which tool to reach for, which flags or
endpoints produce parseable output, what the exit codes/error bodies mean,
how to authenticate against a system that has no local CLI at all, and which
actions are safe to run without asking first.

tool-enabler stores that judgment once per tool, as a YAML **profile**, and
compiles it into every target format so you don't hand-maintain four
near-duplicate context files per project.

## Architecture

```
profiles/*.yaml   →  tool_enabler (loader + renderers)  →  target project:
                                                             .claude/skills/<tool>-cli|api/SKILL.md
                                                             AGENTS.md              (managed section)
                                                             GEMINI.md              (managed section)
                                                             .github/copilot-instructions.md (managed section)
```

- **`profiles/`** — the catalog. One YAML file per tool or system: when to
  use it, canonical commands, output-parsing hints, safety notes on
  side-effecting actions. See `profiles/README.md` for the schema.
- **`tool_enabler/schema.py`** — the data model and validation for a profile.
  Every profile has `interface: cli` (default — a local binary) or
  `interface: api` (an HTTP-only system). The insight that keeps this simple:
  an agent that can already shell out treats "run `gh pr view`" and "run
  `curl https://api.example.com/...`" identically — both are just a command
  in `capabilities[].command`. The only thing an API profile needs that a CLI
  profile doesn't is a documented **auth handshake** (an `api:` block: base
  URL, auth type/header, required env vars, how to obtain credentials, and —
  for systems like Jenkins' CSRF crumb, Splunk's session login, or an OAuth2
  client-credentials exchange — an ordered `session_setup` of prerequisite
  calls). No new execution mechanism was needed to add API coverage.
- **`tool_enabler/render/`** — two renderers back all four targets:
  - `claude_skill.py` → one Skill per tool (Claude Code loads skills
    selectively by description, so each tool gets its own file; the
    description for an `api` profile also lists its required env vars).
  - `markdown.py` → one shared "Tool & API Integrations" section, reused
    verbatim for `AGENTS.md`, `GEMINI.md`, and `copilot-instructions.md`
    since those three all serve the same role (free-form context read once
    per session).
  - `section.py` → writes that shared section into a possibly-pre-existing
    file between `<!-- BEGIN/END TOOL-ENABLER -->` markers, so rebuilding
    never clobbers hand-written content elsewhere in the file.
- **`tool_enabler/cli.py`** — the `tool-enabler` command.

Execution stays with the agent's own shell tool (a CLI binary or `curl`) —
this project only ships context, never a runtime. See "Non-goals" below.

## Install

```bash
cd tool-enabler
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# See what's in the catalog
tool-enabler list

# Sanity-check the catalog after editing a profile
tool-enabler validate

# Pick which tools a given project cares about (writes .tool-enabler.yaml)
tool-enabler init /path/to/some-project --tools gh,git

# Compile into that project — reads .tool-enabler.yaml if present, else all tools
tool-enabler build --target /path/to/some-project

# One-off: only a subset of tools, only some targets
tool-enabler build --target . --tools gh,kubectl --only claude,agents
```

Re-running `build` is idempotent: unchanged output is left untouched, and the
managed markdown sections never touch content outside their markers.

## Catalog

CLI (`interface: cli`): `gh`, `git`, `kubectl`, `aws`, `az`, `gcloud`,
`docker`, `terraform`, `helm`, `npm`, `pip`, `cargo`, `vault`, `jq`.

API (`interface: api`): `jira`, `confluence`, `slack`, `msteams`, `splunk`,
`jenkins`, `harness`, `qtest`.

22 profiles total. Not yet built — candidates for a future pass: `glab`
(GitLab CLI, sibling to `gh`), `psql`/`mysql`/`mongosh` (databases), `stern`
(multi-pod log tailing, complements `kubectl logs`), `argocd`, `uv` (as an
alternative to `pip` — worth a separate profile rather than folding in, since
its command surface and lockfile behavior differ enough to need its own
gotchas documented).

## Adding a tool

See `profiles/README.md`. In short: copy an existing profile — a CLI one
(e.g. `gh.yaml`) or an API one (e.g. `slack.yaml`, or `jenkins.yaml`/
`qtest.yaml` if auth needs more than one step) — fill in `capabilities` with
commands written the way you'd want an agent to actually run them (explicit
`--json`/`output_mode=json` and the like, not bare human-oriented output),
mark side-effecting capabilities `read_only: false`, then `tool-enabler
validate`.

## Non-goals (for now)

- **No MCP execution server.** Agents that can already shell out don't need a
  wrapper to *call* `gh` — they need to know *how*. An MCP adapter that
  surfaces profiles as structured tools for MCP-only clients is a plausible
  phase 2, but the schema above was kept renderer-agnostic so it wouldn't
  require a redesign if that gets built later.
- **Not (yet) a shareable public convention.** This is scoped as a personal/
  team catalog you point at your own projects, not a spec for third-party CLI
  authors to publish profiles against.
