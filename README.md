# tool-enabler

A single catalog of "how to use this tool" knowledge, compiled into the
native context format each GenAI coding agent actually reads — Claude Code
Skills, `AGENTS.md`, `GEMINI.md`, and `.github/copilot-instructions.md`.

Covers two kinds of tool: local **CLIs** (`gh`, `git`, `kubectl`, `aws`, ...)
and systems reachable only over **HTTP APIs** (Jira, Confluence, Slack, MS
Teams, Splunk, Jenkins, Harness, qTest). Both are documented the same way —
see [Architecture](#architecture) below. It also supports adding **your own
custom tool** — an internal CLI or service your team built — as a first-class
profile, without needing to fork or touch this repo's own catalog.

## Table of contents

- [Why](#why)
- [Quickstart](#quickstart)
- [Core concepts](#core-concepts)
- [Architecture](#architecture)
- [Install](#install)
- [CLI reference](#cli-reference)
- [Catalog](#catalog)
- [Adding your own custom tool](#adding-your-own-custom-tool)
- [Documentation](#documentation)
- [Non-goals](#non-goals-for-now)

## Why

Agents like Claude Code, Copilot, Gemini CLI, and Codex CLI can already run
`gh`, `kubectl`, `aws`, `git`, or a `curl` call via their shell tool — the gap
isn't *execution*, it's *judgment*: which tool to reach for, which flags or
endpoints produce parseable output, what the exit codes/error bodies mean,
how to authenticate against a system that has no local CLI at all, what to
do when the tool turns out to be missing or unauthenticated, and which
actions are safe to run without asking first.

tool-enabler stores that judgment once per tool, as a YAML **profile**, and
compiles it into every target format so you don't hand-maintain four
near-duplicate context files per project.

## Quickstart

```bash
git clone https://github.com/roberjo/tool-enabler.git
cd tool-enabler
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

tool-enabler list                                  # what's in the catalog
tool-enabler init /path/to/your/project --tools gh,git,docker
tool-enabler build --target /path/to/your/project  # generates Skills, AGENTS.md, etc.
```

Open `/path/to/your/project/AGENTS.md` and look for the section between
`<!-- BEGIN TOOL-ENABLER -->` and `<!-- END TOOL-ENABLER -->` — that's the
generated content; everything else in the file is left untouched. For the
slower, narrated version of this same path, see
[docs/getting-started.md](docs/getting-started.md).

## Core concepts

If you're new to this space, the four generated file types map to four
different ways coding agents pick up project context:

| Concept | What it is |
|---|---|
| **Profile** | One YAML file in a catalog directory describing one tool or system — when to use it, exact commands, how to parse output, auth setup. The single source of truth. |
| **Catalog** | A directory of profile YAML files. This repo's `profiles/` is the public catalog; you can also point at your own directory of custom/private profiles (see [below](#adding-your-own-custom-tool)), and even merge several catalogs together in one build. |
| **Target** | A project directory to compile profiles *into*. |
| **Claude Code Skill** | A `.claude/skills/<name>/SKILL.md` file with a frontmatter `description` — Claude Code loads a skill's full content only when the description matches what you're doing, so each tool gets its own file. |
| **AGENTS.md / GEMINI.md / copilot-instructions.md** | Plain context files read as ambient background by Codex-family tools, Gemini CLI, and GitHub Copilot respectively — one file, always in context, not selectively loaded. tool-enabler writes the same generated section into all three, since they serve the same purpose for their respective agent. |

## Architecture

```
profiles/*.yaml   →  tool_enabler (loader + renderers)  →  target project:
                                                             .claude/skills/<tool>-cli|api/SKILL.md
                                                             AGENTS.md              (managed section)
                                                             GEMINI.md              (managed section)
                                                             .github/copilot-instructions.md (managed section)
```

- **`profiles/`** — the public catalog. One YAML file per tool or system: when
  to use it, canonical commands, output-parsing hints, safety notes on
  side-effecting actions, and what to do if it's missing or unauthenticated.
  See [profiles/README.md](profiles/README.md) for the full schema.
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
- **`tool_enabler/loader.py`** — reads and validates one catalog directory
  (`load_catalog`), or merges several (`load_catalogs`) — the mechanism
  behind combining the public catalog with your own private one in a single
  build.
- **`tool_enabler/scaffold.py`** — the skeleton YAML `tool-enabler new`
  writes for a brand-new profile.
- **`tool_enabler/render/`** — two renderers back all four targets:
  - `claude_skill.py` → one Skill per tool (Claude Code loads skills
    selectively by description, so each tool gets its own file; the
    description also flags when a profile covers install/auth setup so the
    skill still matches while the tool is missing or unauthenticated).
  - `markdown.py` → one shared "Tool & API Integrations" section, reused
    verbatim for `AGENTS.md`, `GEMINI.md`, and `copilot-instructions.md`
    since those three all serve the same role (free-form context read once
    per session).
  - `section.py` → writes that shared section into a possibly-pre-existing
    file between `<!-- BEGIN/END TOOL-ENABLER -->` markers, so rebuilding
    never clobbers hand-written content elsewhere in the file.
- **`tool_enabler/cli.py`** — the `tool-enabler` command (`list`, `validate`,
  `init`, `build`, `new`).

Execution stays with the agent's own shell tool (a CLI binary or `curl`) —
this project only ships context, never a runtime. See
[Non-goals](#non-goals-for-now) below.

## Install

Prerequisites: Python 3.9+ and `git`. No other runtime dependencies —
`pip install -e .` pulls in the one library used (PyYAML).

```bash
git clone https://github.com/roberjo/tool-enabler.git
cd tool-enabler
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

`-e` (editable) means the `tool-enabler` command runs directly against this
checkout — editing a profile or the compiler source takes effect immediately,
no reinstall step.

## CLI reference

Every subcommand accepts `--catalog` (comma-separated catalog directories,
merged together; default is this repo's `profiles/`) except where noted.

| Command | Purpose |
|---|---|
| `tool-enabler list` | List every profile in the catalog(s), with category and interface. |
| `tool-enabler validate` | Check every profile is well-formed YAML matching the schema. Doesn't check the *content* is filled in — see the [FAQ](docs/faq.md#tool-enabler-new-scaffolded-a-file-and-validate-says-its-fine--am-i-done). |
| `tool-enabler new <name> [--interface cli\|api] [--force]` | Scaffold a new profile skeleton — the starting point for your own custom tool. Takes exactly one `--catalog` directory to write into. |
| `tool-enabler init <target> [--tools a,b,c] [--force]` | Write a `.tool-enabler.yaml` manifest into a target project recording which profiles it wants, so future `build` runs don't need `--tools` repeated. |
| `tool-enabler build [--target .] [--tools a,b,c] [--only claude,agents,gemini,copilot]` | Render the selected profiles into the target project. Reads `.tool-enabler.yaml` if present and `--tools` is omitted; otherwise compiles the whole catalog. Idempotent — unchanged output is left alone, and the managed section overwrites *only itself*, not anything else in the file. |

Two behaviors worth knowing up front:

- **`build` is a full replacement of its own managed section, not additive.**
  Running it twice with different `--tools` values doesn't merge the two
  sets — the second run's tool list is all that remains. Always pass the
  complete set you want (or use a `.tool-enabler.yaml` manifest so you don't
  have to retype it). Details: [FAQ](docs/faq.md#i-ran-build-twice-with-different---tools-and-lost-the-first-set--is-that-a-bug).
- **`--catalog` merges multiple directories.** `--catalog
  profiles,~/my-org/agent-tool-profiles` combines the public catalog with
  your own private one in a single build; a duplicate profile `name` across
  catalogs is a hard error, not a silent pick.

## Catalog

CLI (`interface: cli`): `gh`, `glab`, `git`, `kubectl`, `helm`, `stern`,
`argocd`, `aws`, `az`, `gcloud`, `docker`, `compose` (docker compose),
`terraform`, `npm`, `pip`, `uv`, `cargo`, `vault`, `ssh`, `psql`, `mysql`,
`mongosh`, `redis`, `jq`.

API (`interface: api`): `jira`, `confluence`, `slack`, `msteams`, `splunk`,
`jenkins`, `harness`, `qtest`.

32 profiles total (`tool-enabler list` is always the current, authoritative
listing). Candidates for a future pass, lower priority than what's here:
`openssl`/`age` (crypto), `systemctl` (service management — more sysadmin
than SWE, borderline in scope), a second cloud-observability API profile
(Datadog, PagerDuty) alongside Splunk.

## Adding your own custom tool

Built an internal CLI or service you want your agent to know about? This is
a first-class use case, not an afterthought:

```bash
tool-enabler new my-internal-tool --catalog ~/my-org/agent-tool-profiles
# fill in the TODOs the scaffold prints out, then:
tool-enabler validate --catalog ~/my-org/agent-tool-profiles
tool-enabler build --catalog profiles,~/my-org/agent-tool-profiles --target .
```

Your custom profiles live in your own directory — nothing about this
requires forking or contributing to this repo, and `--catalog` merges your
directory with the public one in one build. See
**[docs/custom-tools.md](docs/custom-tools.md)** for a complete worked
example (a fictional internal deploy CLI, filled in field by field) and
notes on what changes for a tool with internal-only install/auth flows.

If your tool is publicly available and generically useful, consider
contributing the profile back — see the end of that same doc.

## Documentation

- **[docs/getting-started.md](docs/getting-started.md)** — the narrated,
  step-by-step version of the quickstart above.
- **[docs/custom-tools.md](docs/custom-tools.md)** — adding your own custom
  CLI tool or internal service, worked example included.
- **[docs/faq.md](docs/faq.md)** — troubleshooting and gotchas (the
  build-is-a-replacement-not-a-merge behavior, multi-catalog duplicates,
  what `validate` does and doesn't check, and more).
- **[profiles/README.md](profiles/README.md)** — the full profile schema
  reference, field by field, plus the checklist for adding or editing a
  profile.

## Non-goals (for now)

- **No MCP execution server.** Agents that can already shell out don't need a
  wrapper to *call* `gh` — they need to know *how*. An MCP adapter that
  surfaces profiles as structured tools for MCP-only clients is a plausible
  future addition, but the schema was kept renderer-agnostic so it wouldn't
  require a redesign if that gets built later.
- **Not a formal, versioned public spec (yet).** Multi-catalog support and
  `tool-enabler new` make it easy for a team to maintain its own private
  profiles alongside the public catalog, but this project isn't (yet)
  publishing a stable spec for unrelated third parties to build tooling
  against independently.
