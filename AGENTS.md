# Copilot Instructions for `auto-pts`

When generating or modifying Python code in this repository:

- Follow PEP 8 style guidelines.
- Use Python type hints for function signatures, return values, class attributes, and important variables.
- Add clear documentation for all fields and parameters (including class/data attributes and function arguments).
- Prefer docstrings that explain purpose, expected types, valid ranges/values, and behavior.
- Keep changes consistent with this repository's Ruff configuration in `/pyproject.toml`.
- Suggest adding unit tests for new functions
- Treat all functions named `hdl_wid_<id>` as handlers for remote MMI/WID requests; use `params.description` verbatim (PTS-defined) rather than hardcoding prompt text.
