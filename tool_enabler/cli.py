from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from tool_enabler.loader import filter_profiles, load_catalog
from tool_enabler.render.claude_skill import render_skill
from tool_enabler.render.markdown import render_catalog_markdown
from tool_enabler.render.section import upsert_section
from tool_enabler.schema import ProfileError

DEFAULT_CATALOG = Path(__file__).resolve().parent.parent / "profiles"

ALL_TARGETS = ["claude", "agents", "gemini", "copilot"]

TARGET_FILES = {
    "agents": "AGENTS.md",
    "gemini": "GEMINI.md",
    "copilot": ".github/copilot-instructions.md",
}

MANIFEST_NAME = ".tool-enabler.yaml"


def _load_manifest_tools(target: Path) -> list[str] | None:
    manifest_path = target / MANIFEST_NAME
    if not manifest_path.exists():
        return None
    with manifest_path.open() as f:
        data = yaml.safe_load(f) or {}
    tools = data.get("tools")
    if tools is None:
        return None
    return list(tools)


def cmd_list(args: argparse.Namespace) -> int:
    try:
        profiles = load_catalog(Path(args.catalog))
    except (ProfileError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if not profiles:
        print("(no profiles found)")
        return 0
    width = max(len(p.name) for p in profiles)
    for p in profiles:
        tags = [t for t in (p.category, "api" if p.interface == "api" else "") if t]
        suffix = f" [{', '.join(tags)}]" if tags else ""
        print(f"{p.name.ljust(width)}  {p.display_name}{suffix}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        profiles = load_catalog(Path(args.catalog))
    except (ProfileError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"{len(profiles)} profile(s) valid.")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    catalog_dir = Path(args.catalog)
    target_dir = Path(args.target)

    try:
        catalog = load_catalog(catalog_dir)
    except (ProfileError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    requested_names = args.tools.split(",") if args.tools else _load_manifest_tools(target_dir)
    try:
        profiles = filter_profiles(catalog, requested_names)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not profiles:
        print("error: no tool profiles selected (empty catalog or empty --tools list)", file=sys.stderr)
        return 1

    targets = args.only.split(",") if args.only else ALL_TARGETS
    unknown = [t for t in targets if t not in ALL_TARGETS]
    if unknown:
        print(f"error: unknown target(s) {unknown}. Choose from {ALL_TARGETS}", file=sys.stderr)
        return 1

    changed: list[str] = []

    if "claude" in targets:
        skills_dir = target_dir / ".claude" / "skills"
        for p in profiles:
            slug, content = render_skill(p)
            skill_path = skills_dir / slug / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            if not skill_path.exists() or skill_path.read_text() != content:
                skill_path.write_text(content)
                changed.append(str(skill_path.relative_to(target_dir)))

    shared_targets = [t for t in targets if t in TARGET_FILES]
    if shared_targets:
        body = render_catalog_markdown(profiles)
        for t in shared_targets:
            out_path = target_dir / TARGET_FILES[t]
            if upsert_section(out_path, body):
                changed.append(str(out_path.relative_to(target_dir)))

    tool_names = ", ".join(p.name for p in profiles)
    print(f"Built {len(profiles)} tool profile(s) [{tool_names}] -> {target_dir}")
    if changed:
        print("Changed files:")
        for c in changed:
            print(f"  {c}")
    else:
        print("Everything already up to date.")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    target_dir = Path(args.target)
    manifest_path = target_dir / MANIFEST_NAME
    if manifest_path.exists() and not args.force:
        print(f"error: {manifest_path} already exists (use --force to overwrite)", file=sys.stderr)
        return 1

    try:
        catalog = load_catalog(Path(args.catalog))
    except (ProfileError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    tools = args.tools.split(",") if args.tools else [p.name for p in catalog]
    try:
        filter_profiles(catalog, tools)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        "# Which tool-enabler CLI tool profiles to compile into this project.\n"
        "# Run `tool-enabler build --target .` after editing this list.\n"
        f"tools:\n" + "".join(f"  - {t}\n" for t in tools)
    )
    print(f"Wrote {manifest_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tool-enabler",
        description="Compile CLI tool profiles into context files GenAI coding agents read.",
    )
    catalog_parent = argparse.ArgumentParser(add_help=False)
    catalog_parent.add_argument(
        "--catalog",
        default=str(DEFAULT_CATALOG),
        help=f"path to the profiles catalog directory (default: {DEFAULT_CATALOG})",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser(
        "list", parents=[catalog_parent], help="list available tool profiles in the catalog"
    )
    p_list.set_defaults(func=cmd_list)

    p_validate = sub.add_parser(
        "validate", parents=[catalog_parent], help="validate all profiles in the catalog"
    )
    p_validate.set_defaults(func=cmd_validate)

    p_init = sub.add_parser(
        "init",
        parents=[catalog_parent],
        help="scaffold a .tool-enabler.yaml in a target project",
    )
    p_init.add_argument("target", help="target project directory")
    p_init.add_argument("--tools", help="comma-separated profile names (default: all)")
    p_init.add_argument("--force", action="store_true", help="overwrite an existing manifest")
    p_init.set_defaults(func=cmd_init)

    p_build = sub.add_parser(
        "build", parents=[catalog_parent], help="render profiles into a target project"
    )
    p_build.add_argument("--target", default=".", help="target project directory (default: .)")
    p_build.add_argument(
        "--tools",
        help="comma-separated profile names to include (default: .tool-enabler.yaml, else all)",
    )
    p_build.add_argument(
        "--only",
        help=f"comma-separated targets to render: {ALL_TARGETS} (default: all)",
    )
    p_build.set_defaults(func=cmd_build)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
