# Profile schema

Each `*.yaml` file in this directory is one Tool Profile — the single source
of truth for how GenAI coding agents should use that tool or system.
Validation rules live in `tool_enabler/schema.py`; this is the human-readable
reference.

A profile is either `interface: cli` (a local binary, the default) or
`interface: api` (a system reachable only over HTTP — Jira, Slack, Splunk,
etc.). Both use the same `capabilities` shape: `command` is what the agent
actually runs, whether that's a CLI invocation or a `curl` call against a
documented endpoint. The `api` block only exists to carry what a bare
endpoint list can't — the auth handshake.

```yaml
name: gh                 # required, slug, matches the filename convention
display_name: GitHub CLI # required
interface: cli             # optional, "cli" (default) or "api"
binary: gh                 # required when interface: cli — the executable name
homepage: https://...      # optional
category: vcs-hosting      # optional, free text — used only for `tool-enabler list`

detect:
  installed_check: "gh --version"     # optional — command to confirm the binary exists (cli only)
  auth_check: "gh auth status"        # optional — cheap command/curl call to confirm auth works
  install_hint: "brew install gh"     # optional — shown to the agent if missing (cli only)

# api: block — required when interface: api, ignored for interface: cli
api:
  base_url: "https://api.example.com"   # required for interface: api; {placeholders} for per-org values
  auth:
    type: "bearer_token"                 # free text — a label, not an enum (bearer_token, basic_api_token,
                                          # oauth2_client_credentials, oauth2_password_grant, api_key, webhook, ...)
    header: "Authorization: Bearer $EXAMPLE_TOKEN"   # the header shape, referencing an env var
    env_vars: ["EXAMPLE_TOKEN"]           # names the agent should read credentials from — never inline a secret
    how_to_obtain: "..."                  # where/how a human sets these env vars up once
    session_setup:                        # optional — ordered commands to run first when auth is a
      - "curl ... /oauth/token ..."       # multi-step handshake (OAuth2 client-credentials, Jenkins CSRF
                                           # crumbs, Splunk session login) rather than a single static header
    notes: "..."                          # token lifetime, revocation behavior, anything non-obvious
  rate_limits: "..."                     # optional — free text

when_to_use:                 # optional list of strings — concrete tasks this tool covers
  - "..."

prefer_over:                 # optional — when to reach for this over an alternative
  - tool: "web browser"
    reason: "..."

capabilities:                # required, at least one entry
  - task: "..."               # required — what this accomplishes
    method: "GET"              # optional, api profiles only — for readability, doesn't affect execution
    path: "/issue/{id}"        # optional, api profiles only — same
    command: "..."            # required — canonical invocation (CLI command or curl call), {placeholders} for args
    notes: "..."              # optional — gotchas specific to this invocation
    example_output: "..."     # optional — a realistic sample of the output shape
    read_only: true            # default true; set false for anything side-effecting

output_parsing:               # optional
  json_flag: "--json <fields>"        # the flag/param that forces structured output, if any
                                       # (e.g. "output_mode=json" for a query-string system)
  common_fields:
    - path: ".state"
      meaning: "OPEN | CLOSED | MERGED"
  error_handling:
    - exit_code: 1               # either exit_code or pattern
      meaning: "..."
    - pattern: "not authenticated"
      meaning: "..."

pitfalls:                     # optional list of strings
  - "..."
```

## `interface: api` conventions worth keeping consistent

- **Never inline a credential.** `header`/`command` reference `$ENV_VAR` names;
  `env_vars` lists what the agent (or the human setting up the project)
  actually needs to export. This is the one rule every API profile in this
  catalog follows — keep it that way when adding more.
- **Use `session_setup` for multi-step auth**, not a workaround crammed into
  `command`. See `jenkins.yaml` (CSRF crumb), `splunk.yaml` (session login),
  `msteams.yaml` and `qtest.yaml` (OAuth2 token exchange) for the pattern.
- **Call out that curl doesn't fail on HTTP error status** — nearly every API
  profile's `pitfalls` repeats this because it's the single most common way
  an agent misreads a rejected write as success. Keep repeating it in new
  profiles rather than assuming it's obvious.
- **Add a "verify against current docs" pitfall** for any fast-moving SaaS
  API. Endpoint shapes and deprecations (see `msteams.yaml`'s webhook note)
  change after this profile was written.

## Adding a new tool

1. Copy an existing profile as a starting point.
2. Fill in `capabilities` first — this is the only required section, and it's
   the part that actually saves the agent from guessing flags. Write commands
   the way you'd want an agent to actually run them (explicit `--json` fields,
   not bare human-oriented invocations).
3. Mark every capability's `read_only` accurately — this flows into the
   generated docs as a confirm-before-running note for side-effecting
   commands.
4. Run `tool-enabler validate` to check the file loads.
5. Run `tool-enabler build --target <some project>` to see the generated
   output before committing.
