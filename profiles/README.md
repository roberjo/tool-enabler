# Profile schema

Each `*.yaml` file in this directory is one CLI Tool Profile — the single
source of truth for how GenAI coding agents should use that tool. Validation
rules live in `tool_enabler/schema.py`; this is the human-readable reference.

```yaml
name: gh                 # required, slug, matches the filename convention
display_name: GitHub CLI # required
binary: gh                # required, the actual executable name
homepage: https://...      # optional
category: vcs-hosting      # optional, free text — used only for `tool-enabler list`

detect:
  installed_check: "gh --version"     # optional — command to confirm the binary exists
  auth_check: "gh auth status"        # optional — command to confirm it's authenticated
  install_hint: "brew install gh"     # optional — shown to the agent if missing

when_to_use:                 # optional list of strings — concrete tasks this tool covers
  - "..."

prefer_over:                 # optional — when to reach for this over an alternative
  - tool: "web browser"
    reason: "..."

capabilities:                # required, at least one entry
  - task: "..."               # required — what this accomplishes
    command: "..."            # required — canonical invocation, {placeholders} for args
    notes: "..."              # optional — gotchas specific to this invocation
    example_output: "..."     # optional — a realistic sample of the output shape
    read_only: true            # default true; set false for anything side-effecting

output_parsing:               # optional
  json_flag: "--json <fields>"        # the flag that forces structured output, if any
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
