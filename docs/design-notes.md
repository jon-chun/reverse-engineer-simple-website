# Design Notes

- This repo is intentionally config-driven because target websites vary in HTML structure.
- Start by adjusting `patterns.*` and `selectors.*` in `config/config.yml` for the target site.
- For JS-rendered pages, enable Playwright and install browser binaries:
  - `python -m playwright install`
