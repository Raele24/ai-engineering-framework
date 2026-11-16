## Summary
<!-- Concise description of what changed and why. -->

## Related Issue / Specification / ADR
- Issue: `#`
- Specification: `docs/specs/...`
- ADR (if applicable): `docs/adr/ADR-...`

## Verification Checklist
- [ ] Canonical sources updated first (`core/`, `agents/`, `skills/`, `workflows/`).
- [ ] Platform adapters synchronized (`python scripts/sync_adapters.py --check` exits `0`).
- [ ] Repository validation passed (`python scripts/validate.py` exits `0`).
- [ ] Automated unit tests passed (`python -m unittest discover -s tests -v`).
- [ ] Zero secrets, tokens, or private keys included.
- [ ] Documentation passes anti-slop review (`skills/core/anti-slop/SKILL.md`).
