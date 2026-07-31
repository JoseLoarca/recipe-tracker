# 0008: Household-visible recipes are owner-only editable

## Status
Accepted

## Context
A recipe can be shared to `household` visibility so both members can see it. The question is whether both members should also be able to *edit* it.

## Decision
Only the owning user can edit a recipe, regardless of its visibility setting. Household visibility controls viewing only, never editing.

## Rationale
- The stated requirement was shared *viewing* ("recipes both want to see"), not shared editing — extending edit rights was never asked for.
- Extraction output is often imperfect and needs correction; allowing any household member to silently modify another person's recipe, with no versioning or audit trail in this MVP, risks unwanted or conflicting changes with no way to recover the prior version.
- If mutual editing becomes genuinely wanted later, the recommended path is an explicit opt-in "co-edit" flag plus an edit history/audit log — not making shared editing the default.
