from __future__ import annotations

from ..config import AppConfig
from ..io.md_writer import write_website_rebuild_spec


def generate(cfg: AppConfig) -> None:
    write_website_rebuild_spec(cfg.docs.tech_spec_path, base_url=cfg.site.base_url)
