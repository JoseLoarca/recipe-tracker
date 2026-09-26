"""Shared enums for recipe visibility, processing status, and macro provenance."""

import enum


class RecipeVisibility(enum.StrEnum):
    """Who besides the owner can see a recipe."""

    PERSONAL = "personal"
    HOUSEHOLD = "household"


class RecipeStatus(enum.StrEnum):
    """A recipe submission's position in the extraction pipeline."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class MacroSource(enum.StrEnum):
    """Where a recipe's or ingredient's macro values came from."""

    USDA_VERIFIED = "usda_verified"
    LLM_ESTIMATED = "llm_estimated"
    MIXED = "mixed"
