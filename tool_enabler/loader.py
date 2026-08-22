"""Load and validate CLI Tool Profiles from a catalog directory of YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml

from tool_enabler.schema import Profile, ProfileError


def load_catalog(profiles_dir: Path) -> list[Profile]:
    """Load every *.yaml/*.yml profile in profiles_dir (non-recursive).

    Raises ProfileError with the offending file path if any profile is invalid.
    """
    if not profiles_dir.is_dir():
        raise FileNotFoundError(f"profiles directory not found: {profiles_dir}")

    profiles: list[Profile] = []
    seen_names: dict[str, Path] = {}
    for path in sorted(profiles_dir.glob("*.yaml")) + sorted(profiles_dir.glob("*.yml")):
        if path.name.startswith("_"):
            continue
        with path.open() as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict):
            raise ProfileError(str(path), "top-level YAML must be a mapping")
        profile = Profile.from_dict(raw, str(path))
        if profile.name in seen_names:
            raise ProfileError(
                str(path),
                f"duplicate profile name '{profile.name}' (also defined in {seen_names[profile.name]})",
            )
        seen_names[profile.name] = path
        profiles.append(profile)
    return profiles


def filter_profiles(profiles: list[Profile], names: list[str] | None) -> list[Profile]:
    """Restrict a catalog to the given profile names, preserving catalog order.

    Raises ValueError listing any requested name not found in the catalog.
    """
    if names is None:
        return profiles
    by_name = {p.name: p for p in profiles}
    missing = [n for n in names if n not in by_name]
    if missing:
        available = ", ".join(sorted(by_name)) or "(none)"
        raise ValueError(
            f"unknown tool profile(s): {', '.join(missing)}. Available: {available}"
        )
    return [by_name[n] for n in names]
