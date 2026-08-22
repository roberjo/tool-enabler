"""Render a Profile into a Claude Code Skill (SKILL.md with YAML frontmatter).

Unlike the shared markdown target, Claude Code Skills are loaded selectively
based on the frontmatter `description`, so each tool gets its own skill
directory rather than one big shared file.
"""

from __future__ import annotations

from tool_enabler.render.markdown import render_tool_section
from tool_enabler.schema import Profile


def _skill_description(p: Profile) -> str:
    subject = p.display_name if p.interface == "api" else f"{p.display_name} (`{p.binary}`)"
    bits = [f"Use when working with {subject}."]
    if p.when_to_use:
        bits.append("Covers: " + "; ".join(p.when_to_use) + ".")
    if p.prefer_over:
        reasons = "; ".join(f"prefer over {po.tool} ({po.reason})" for po in p.prefer_over)
        bits.append(reasons + ".")
    if p.interface == "api" and p.api.auth.env_vars:
        bits.append("Requires env vars: " + ", ".join(p.api.auth.env_vars) + ".")
    bits.append(
        "Also use this if the tool turns out to be missing or not authenticated — "
        "it includes install/auth setup steps."
    )
    return " ".join(bits)


def _yaml_escape(s: str) -> str:
    return s.replace('"', '\\"')


def render_skill(p: Profile) -> tuple[str, str]:
    """Return (skill_slug, skill_md_content)."""
    slug = f"{p.name}-api" if p.interface == "api" else f"{p.name}-cli"
    description = _yaml_escape(_skill_description(p))
    frontmatter = (
        "---\n"
        f'name: {slug}\n'
        f'description: "{description}"\n'
        "---\n"
    )
    section = render_tool_section(p, heading_level=1)
    if p.homepage:
        heading, rest = section.split("\n", 1)
        section = f"{heading}\n\n{p.homepage}\n{rest}"
    return slug, frontmatter + "\n" + section
