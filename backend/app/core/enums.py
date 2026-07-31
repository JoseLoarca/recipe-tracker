import enum


class RecipeVisibility(enum.StrEnum):
    PERSONAL = "personal"
    HOUSEHOLD = "household"


class RecipeStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class MacroSource(enum.StrEnum):
    USDA_VERIFIED = "usda_verified"
    LLM_ESTIMATED = "llm_estimated"
    MIXED = "mixed"
