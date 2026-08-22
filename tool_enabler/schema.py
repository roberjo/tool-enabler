"""Data model for a CLI Tool Profile, plus validation of the raw YAML dict."""

from __future__ import annotations

from dataclasses import dataclass, field


class ProfileError(ValueError):
    """Raised when a profile YAML file is missing required fields or malformed."""

    def __init__(self, source: str, message: str):
        super().__init__(f"{source}: {message}")


def _require(d: dict, key: str, source: str) -> object:
    if key not in d or d[key] in (None, ""):
        raise ProfileError(source, f"missing required field '{key}'")
    return d[key]


def _str_list(d: dict, key: str) -> list[str]:
    return list(d.get(key) or [])


@dataclass
class PreferOver:
    tool: str
    reason: str

    @classmethod
    def from_dict(cls, d: dict, source: str) -> "PreferOver":
        return cls(
            tool=str(_require(d, "tool", source)),
            reason=str(_require(d, "reason", source)),
        )


@dataclass
class Capability:
    task: str
    command: str
    notes: str = ""
    example_output: str = ""
    read_only: bool = True
    method: str = ""
    path: str = ""

    @classmethod
    def from_dict(cls, d: dict, source: str) -> "Capability":
        return cls(
            task=str(_require(d, "task", source)),
            command=str(_require(d, "command", source)),
            notes=str(d.get("notes", "")),
            example_output=str(d.get("example_output", "")),
            read_only=bool(d.get("read_only", True)),
            method=str(d.get("method", "")),
            path=str(d.get("path", "")),
        )


@dataclass
class ErrorHint:
    meaning: str
    exit_code: int | None = None
    pattern: str | None = None

    @classmethod
    def from_dict(cls, d: dict, source: str) -> "ErrorHint":
        return cls(
            meaning=str(_require(d, "meaning", source)),
            exit_code=d.get("exit_code"),
            pattern=d.get("pattern"),
        )


@dataclass
class FieldHint:
    path: str
    meaning: str

    @classmethod
    def from_dict(cls, d: dict, source: str) -> "FieldHint":
        return cls(
            path=str(_require(d, "path", source)),
            meaning=str(_require(d, "meaning", source)),
        )


@dataclass
class OutputParsing:
    json_flag: str = ""
    common_fields: list[FieldHint] = field(default_factory=list)
    error_handling: list[ErrorHint] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict, source: str) -> "OutputParsing":
        return cls(
            json_flag=str(d.get("json_flag", "")),
            common_fields=[
                FieldHint.from_dict(f, source) for f in d.get("common_fields", [])
            ],
            error_handling=[
                ErrorHint.from_dict(e, source) for e in d.get("error_handling", [])
            ],
        )


@dataclass
class Detect:
    installed_check: str = ""
    auth_check: str = ""
    install_hint: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Detect":
        return cls(
            installed_check=str(d.get("installed_check", "")),
            auth_check=str(d.get("auth_check", "")),
            install_hint=str(d.get("install_hint", "")),
        )


@dataclass
class ApiAuth:
    type: str = ""
    header: str = ""
    env_vars: list[str] = field(default_factory=list)
    how_to_obtain: str = ""
    session_setup: list[str] = field(default_factory=list)
    notes: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "ApiAuth":
        return cls(
            type=str(d.get("type", "")),
            header=str(d.get("header", "")),
            env_vars=list(d.get("env_vars") or []),
            how_to_obtain=str(d.get("how_to_obtain", "")),
            session_setup=list(d.get("session_setup") or []),
            notes=str(d.get("notes", "")),
        )


@dataclass
class ApiConfig:
    base_url: str = ""
    auth: ApiAuth = field(default_factory=ApiAuth)
    rate_limits: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "ApiConfig":
        return cls(
            base_url=str(d.get("base_url", "")),
            auth=ApiAuth.from_dict(d.get("auth") or {}),
            rate_limits=str(d.get("rate_limits", "")),
        )


@dataclass
class Profile:
    name: str
    display_name: str
    interface: str = "cli"
    binary: str = ""
    homepage: str = ""
    category: str = ""
    detect: Detect = field(default_factory=Detect)
    api: ApiConfig = field(default_factory=ApiConfig)
    when_to_use: list[str] = field(default_factory=list)
    prefer_over: list[PreferOver] = field(default_factory=list)
    capabilities: list[Capability] = field(default_factory=list)
    output_parsing: OutputParsing = field(default_factory=OutputParsing)
    pitfalls: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict, source: str) -> "Profile":
        name = str(_require(d, "name", source))
        interface = str(d.get("interface", "cli"))
        if interface not in ("cli", "api"):
            raise ProfileError(source, f"'interface' must be 'cli' or 'api', got '{interface}'")

        capabilities = d.get("capabilities") or []
        if not capabilities:
            raise ProfileError(source, "must declare at least one entry in 'capabilities'")

        binary = str(d.get("binary", ""))
        if interface == "cli" and not binary:
            raise ProfileError(source, "interface: cli requires 'binary'")

        api = ApiConfig.from_dict(d.get("api") or {})
        if interface == "api" and not api.base_url:
            raise ProfileError(source, "interface: api requires 'api.base_url'")

        return cls(
            name=name,
            display_name=str(_require(d, "display_name", source)),
            interface=interface,
            binary=binary,
            homepage=str(d.get("homepage", "")),
            category=str(d.get("category", "")),
            detect=Detect.from_dict(d.get("detect") or {}),
            api=api,
            when_to_use=_str_list(d, "when_to_use"),
            prefer_over=[
                PreferOver.from_dict(p, source) for p in d.get("prefer_over", [])
            ],
            capabilities=[Capability.from_dict(c, source) for c in capabilities],
            output_parsing=OutputParsing.from_dict(d.get("output_parsing") or {}, source),
            pitfalls=_str_list(d, "pitfalls"),
        )
