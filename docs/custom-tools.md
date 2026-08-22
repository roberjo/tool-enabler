# Adding your own custom CLI tool

You built an internal tool — a deploy script, a scaffolding CLI, an internal
API wrapper — and you want your AI coding agent to know it exists, when to
reach for it, and how to call it. This is exactly what tool-enabler is for;
nothing about the process is different for a tool you wrote yourself versus
`gh` or `kubectl`. This doc walks through it end to end with a fictional
internal tool, `deploytool`.

## Decide where the profile lives

Two options, and they're not mutually exclusive:

1. **In this repo's `profiles/` directory**, if your tool is generally useful
   and you're happy to contribute it back (see [Contributing](#contributing-a-profile-back) below).
2. **In your own private catalog directory** — a folder anywhere on disk
   (in a private repo, a subfolder of the tool's own repo, wherever makes
   sense for you) holding just your org's custom profiles. `tool-enabler`
   doesn't care where a catalog directory lives; every command that reads a
   catalog takes a `--catalog` path.

For an internal-only tool, option 2 is almost always right — you get the
same generated Skills/AGENTS.md/etc. without needing to fork or contribute to
this repo. This guide uses option 2.

## 1. Scaffold the profile

```bash
tool-enabler new deploytool --catalog ~/my-org/agent-tool-profiles
```

This writes `~/my-org/agent-tool-profiles/deploytool.yaml`, pre-filled with
every schema field and inline comments, and prints the next steps. Use
`--interface api` instead of the default `cli` if your tool is a service
reachable only over HTTP rather than a local binary (see the schema
reference in [profiles/README.md](../profiles/README.md) for what changes).

## 2. Fill in the TODOs

Open the file. Here's what a filled-in version might look like for a
fictional internal deploy CLI that wraps your org's release process:

```yaml
name: deploytool
display_name: "Internal Deploy CLI"
binary: deploytool
homepage: "https://wiki.internal.example.com/deploytool"   # an internal doc is fine
category: "internal-tooling"

detect:
  installed_check: "deploytool --version"
  auth_check: "deploytool whoami"
  install_hint: "Internal artifact — download from https://artifacts.internal.example.com/deploytool/latest, or ask #platform-team for access."
  auth_setup: "Run `deploytool login --sso` (opens a browser against the internal SSO provider)."

when_to_use:
  - "Deploying a service to a named environment (dev/staging/prod)"
  - "Checking a service's currently deployed version before deciding whether a deploy is needed"

prefer_over:
  - tool: "manually SSHing into hosts or running raw kubectl against the deploy pipeline"
    reason: "deploytool wraps the org's approval/rollback process; bypassing it skips required checks"

capabilities:
  - task: "Check what's currently deployed to an environment"
    command: "deploytool status --env {env} --json"
    read_only: true

  - task: "Deploy a specific version to an environment"
    command: "deploytool deploy --env {env} --version {version}"
    notes: "Side-effecting and visible to the whole org. Non-prod environments are low risk; prod deploys should always be confirmed explicitly, and check whether the org requires a change ticket first."
    read_only: false

  - task: "Roll back to the previous version"
    command: "deploytool rollback --env {env}"
    read_only: false

output_parsing:
  json_flag: "--json"
  common_fields:
    - path: ".version"
      meaning: "the currently deployed version string"
    - path: ".status"
      meaning: "healthy | degraded | deploying | failed"

pitfalls:
  - "Deploys to prod require an approved change ticket per org policy — deploytool doesn't enforce this itself, it just executes the deploy, so check with the user rather than assuming a request to 'deploy to prod' has already been approved."
  - "--env is case-sensitive and org-specific (dev/staging/prod, not Dev/Staging/Prod) — check `deploytool status` output for the exact spelling used in this org before guessing."
```

The same principles from the rest of the catalog apply here — see
[profiles/README.md](../profiles/README.md#adding-a-new-tool) for the full
checklist. A few things worth calling out for an internal tool specifically:

- **`install_hint` and `auth_setup` won't point at Homebrew or a public
  login flow** — that's expected. Say plainly where to get the binary
  (an internal artifact server, a Slack channel to ask in) and how auth
  actually works here (SSO, an internal token, a config file populated by
  onboarding). An agent that hits "not installed" or "not authenticated"
  needs a real next step, even if that step is "ask a human."
- **`homepage` can point at an internal wiki page** instead of a public URL —
  it's just a reference link, nothing resolves it.
- **Lean on `pitfalls` for anything org-specific** an agent wouldn't be able
  to infer: naming conventions, approval processes, environments that don't
  behave like the others.

## 3. Validate

```bash
tool-enabler validate --catalog ~/my-org/agent-tool-profiles
```

## 4. Build it into a project — alone, or combined with the public catalog

Just your custom tool:

```bash
tool-enabler build --catalog ~/my-org/agent-tool-profiles --target . --tools deploytool
```

Combined with the public catalog (`gh`, `docker`, etc.) in one build,
`--catalog` takes a comma-separated list and merges them:

```bash
tool-enabler build \
  --catalog /path/to/tool-enabler/profiles,~/my-org/agent-tool-profiles \
  --target . \
  --tools gh,docker,deploytool
```

If the same profile name exists in both catalogs, `build`/`validate`/`list`
all fail loudly with a "duplicate profile name" error rather than silently
picking one — rename one of them if that happens.

For a project you rebuild regularly, avoid retyping the long `--catalog`
flag by wrapping the command in a small script or Makefile target checked
into the project — `.tool-enabler.yaml` itself only records which `tools:`
to include, not which catalog directories to read them from.

## 5. Confirm it worked

Check `.claude/skills/deploytool-cli/SKILL.md` and the generated section in
`AGENTS.md`/`GEMINI.md`/`.github/copilot-instructions.md`. Try asking your
agent to do something the profile covers ("what's currently deployed to
staging?") and see whether it reaches for `deploytool status` unprompted.

## Contributing a profile back

If your tool is publicly available (or the profile is generically useful —
e.g. you wrote a profile for a popular open-source CLI that isn't in the
catalog yet), consider contributing it back:

1. Copy your profile into this repo's `profiles/` directory.
2. Strip anything genuinely org-internal (internal URLs, SSO specifics) and
   replace with the public equivalent.
3. Run `tool-enabler validate` and a scratch `build` to confirm it renders
   cleanly (see [getting-started.md](getting-started.md)).
4. Open a PR.
