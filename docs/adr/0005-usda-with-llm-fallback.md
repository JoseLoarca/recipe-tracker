# 0005: USDA FoodData Central as source of truth, LLM estimate as fallback only

## Status
Accepted

## Context
Macro accuracy matters to the user (tracking body composition), but a fully automated pipeline can't guarantee every extracted ingredient matches a USDA database entry, and the USDA API can be unavailable.

## Decision
Always attempt to resolve each ingredient's macros against the USDA FoodData Central API first. Only fall back to an LLM-generated estimate when the API is unreachable or the ingredient isn't found — never the reverse. Every ingredient and recipe records which method produced its macros (`usda_verified` / `llm_estimated` / `mixed`).

## Rationale
- USDA data is authoritative and free; defaulting to it maximizes accuracy without any cost.
- A silent, unlabeled LLM estimate could mislead someone making dietary decisions based on it — labeling the source lets the user judge how much to trust a given number.
- Falling back per-ingredient (rather than failing the whole recipe) means a single unmatched ingredient doesn't block the rest of the extraction.
