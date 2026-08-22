"""Render a Profile (or list of Profiles) into the Markdown shape shared by
AGENTS.md, GEMINI.md, and .github/copilot-instructions.md.

These three files all serve the same purpose for their respective agents:
free-form context read once per session. There is no reason to render them
differently, so one function backs all three targets.
"""

from __future__ import annotations

from tool_enabler.schema import Profile


def _heading_subject(p: Profile) -> str:
    if p.interface == "api":
        return p.display_name
    return f"{p.display_name} (`{p.binary}`)"


def render_tool_section(p: Profile, heading_level: int = 3) -> str:
    h = "#" * heading_level
    lines: list[str] = []
    lines.append(f"{h} {_heading_subject(p)}")
    lines.append("")

    if p.when_to_use:
        lines.append("**When to use:**")
        for item in p.when_to_use:
            lines.append(f"- {item}")
        lines.append("")

    if p.prefer_over:
        lines.append("**Prefer over:**")
        for po in p.prefer_over:
            lines.append(f"- {po.tool} — {po.reason}")
        lines.append("")

    detect_bits = []
    if p.detect.installed_check:
        detect_bits.append(f"installed: `{p.detect.installed_check}`")
    if p.detect.auth_check:
        detect_bits.append(f"authenticated: `{p.detect.auth_check}`")
    if detect_bits:
        line = "**Check availability:** " + "; ".join(detect_bits)
        if p.detect.install_hint:
            line += f". If missing: `{p.detect.install_hint}`"
        lines.append(line)
        lines.append("")

    if p.interface == "api":
        a = p.api.auth
        lines.append(f"**Interface:** REST API — base URL `{p.api.base_url}`")
        lines.append("")
        auth_bits = []
        if a.type:
            auth_bits.append(f"type `{a.type}`")
        if a.header:
            auth_bits.append(f"header: `{a.header}`")
        lines.append("**Auth:** " + (", ".join(auth_bits) if auth_bits else "(see notes)"))
        if a.env_vars:
            lines.append(f"- Required env vars: {', '.join(f'`{v}`' for v in a.env_vars)}")
        if a.how_to_obtain:
            lines.append(f"- How to obtain: {a.how_to_obtain}")
        if a.session_setup:
            lines.append("- Session setup (run first, in order):")
            for i, step in enumerate(a.session_setup, 1):
                lines.append(f"  {i}. `{step}`")
        if a.notes:
            lines.append(f"- {a.notes}")
        lines.append(
            "- Never print, log, or commit token/credential values — read them from "
            "env vars or a secret manager only."
        )
        if p.api.rate_limits:
            lines.append(f"- Rate limits: {p.api.rate_limits}")
        lines.append("")

    if p.capabilities:
        lines.append("**Capabilities:**")
        for c in p.capabilities:
            tag = "read-only" if c.read_only else "side-effecting — confirm before running"
            lines.append(f"- {c.task} ({tag})")
            if c.method and c.path:
                lines.append(f"  `{c.method} {c.path}`")
            lines.append(f"  `{c.command}`")
            if c.notes:
                lines.append(f"  {c.notes}")
        lines.append("")

    op = p.output_parsing
    if op.json_flag or op.common_fields or op.error_handling:
        lines.append("**Output parsing:**")
        if op.json_flag:
            lines.append(f"- Structured output flag: `{op.json_flag}`")
        for f in op.common_fields:
            lines.append(f"- `{f.path}` → {f.meaning}")
        for e in op.error_handling:
            if e.exit_code is not None:
                lines.append(f"- Exit code {e.exit_code} → {e.meaning}")
            elif e.pattern:
                lines.append(f"- Message matching `{e.pattern}` → {e.meaning}")
        lines.append("")

    if p.pitfalls:
        lines.append("**Pitfalls:**")
        for item in p.pitfalls:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_catalog_markdown(profiles: list[Profile]) -> str:
    """Render the full 'Tool & API Integrations' body shared across
    AGENTS.md/GEMINI.md/copilot-instructions.md."""
    parts = ["## Tool & API Integrations", ""]
    parts.append(
        "The following CLI tools and API-based systems are available in this "
        "environment. Prefer them over slower or less reliable alternatives "
        "(web UI clicking, ad-hoc scraping) when they cover the task. API "
        "systems are called the same way as CLI tools — with `curl` via your "
        "shell tool — the difference is the auth handshake documented below."
    )
    parts.append("")
    for i, p in enumerate(profiles):
        parts.append(render_tool_section(p))
        if i != len(profiles) - 1:
            parts.append("---")
            parts.append("")
    return "\n".join(parts).rstrip() + "\n"
