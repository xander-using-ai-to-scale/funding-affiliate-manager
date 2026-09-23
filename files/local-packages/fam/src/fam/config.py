"""Runtime configuration: paths, GHL map, cadence rules, and policy.

Everything that differs between a demo location and a client location lives in
config/*.json or the environment, so duplicating the system is a config change.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import FamError

PACKAGE_ROOT = Path(__file__).resolve().parents[2]  # files/local-packages/fam
REPO_ROOT = PACKAGE_ROOT.parents[2]  # repo root when running from a checkout

CUSTOM_FIELD_KEYS = (
    "affiliate_id",
    "join_date",
    "source",
    "niche",
    "audience_size",
    "deals_submitted",
    "last_deal_date",
    "funded_volume",
    "last_touch_date",
    "last_touch_channel",
    "last_offer_date",
    "last_reply_date",
    "next_touch_date",
    "cadence_note",
    "preferred_channel",
    "assigned_manager",
    "products_of_interest",
    "services_offered",
    "obsidian_note",
)

DEFAULT_CADENCE: dict[str, Any] = {
    "onboarding_days": 14,
    "biweekly_touch_days": 14,
    "monthly_offer_days": 30,
    "quiet_after_days": 45,
    "checkin_after_days": 60,
    "dormant_after_days": 90,
    "dead_after_days": 180,
    "dead_reactivation_every_days": 90,
    "sms_window_start_hour": 11,
    "sms_window_end_hour": 20,
    "daily_personal_touch_cap": 40,
    "daily_bulk_enroll_cap": 2000,
    "batch_approval_max": 100,
    "approval_ttl_hours": 12,
    "timezone": "America/New_York",
}


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name, "").strip()
    return Path(value).expanduser() if value else default


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise FamError(f"{path.name} is not valid JSON: {exc}") from exc


@dataclass
class Settings:
    config_dir: Path
    state_dir: Path
    vault_dir: Path
    policy_path: Path
    ghl_mode: str
    demo_mode: bool
    profile: str
    ghl_map: dict[str, Any] = field(default_factory=dict)
    cadence: dict[str, Any] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Settings":
        config_dir = _env_path("FAM_CONFIG_DIR", REPO_ROOT / "config")
        state_dir = _env_path("FAM_STATE_DIR", Path.home() / ".fam" / "state")
        vault_dir = _env_path("FAM_VAULT_DIR", Path.home() / "fam-vault")
        policy_path = _env_path("FAM_POLICY_PATH", REPO_ROOT / "policies" / "permissions.json")
        ghl_mode = os.getenv("FAM_GHL_MODE", "live").strip().lower() or "live"
        if ghl_mode not in {"live", "mock"}:
            raise FamError("FAM_GHL_MODE must be 'live' or 'mock'")
        demo_mode = os.getenv("FAM_DEMO_MODE", "1").strip() not in {"0", "false", "no"}
        ghl_map = _read_json(config_dir / "ghl-map.json", {})
        cadence = dict(DEFAULT_CADENCE)
        cadence.update(_read_json(config_dir / "cadence.json", {}))
        policy = _read_json(policy_path, {})
        profile = os.getenv("FAM_GHL_PROFILE", "").strip() or str(ghl_map.get("profile", ""))
        state_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            config_dir=config_dir,
            state_dir=state_dir,
            vault_dir=vault_dir,
            policy_path=policy_path,
            ghl_mode=ghl_mode,
            demo_mode=demo_mode,
            profile=profile,
            ghl_map=ghl_map,
            cadence=cadence,
            policy=policy,
        )

    # ── GHL map helpers ────────────────────────────────────────────────────
    def field_id(self, key: str) -> str:
        """Return the GHL custom-field id for a logical key (mock mode uses the key)."""
        if self.ghl_mode == "mock":
            return key
        ids = self.ghl_map.get("custom_fields", {})
        value = ids.get(key, "")
        if not value:
            raise FamError(
                f"custom field '{key}' has no GHL id in config/ghl-map.json — run `fam ghl bootstrap` first"
            )
        return value

    def field_ids(self) -> dict[str, str]:
        if self.ghl_mode == "mock":
            return {key: key for key in CUSTOM_FIELD_KEYS}
        return {k: v for k, v in self.ghl_map.get("custom_fields", {}).items() if v}

    def workflow_id(self, key: str) -> str:
        value = self.ghl_map.get("workflows", {}).get(key, "")
        if self.ghl_mode == "mock":
            return value or f"wf-{key}"
        if not value:
            raise FamError(f"workflow '{key}' is not mapped in config/ghl-map.json")
        return value

    def pipeline(self, key: str) -> dict[str, Any]:
        pipelines = self.ghl_map.get("pipelines", {})
        value = pipelines.get(key) or {}
        if self.ghl_mode == "mock" and not value.get("id"):
            spec = _read_json(self.config_dir / "pipelines.json", {}).get(key, {})
            return {
                "id": f"pl-{key}",
                "stages": {stage: f"st-{key}-{stage}" for stage in spec.get("stages", [])},
            }
        if not value.get("id"):
            raise FamError(f"pipeline '{key}' is not mapped in config/ghl-map.json")
        return value

    def policy_rule(self, action: str) -> dict[str, Any]:
        return self.policy.get("actions", {}).get(action, {})
