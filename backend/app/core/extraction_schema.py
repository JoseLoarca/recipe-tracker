"""Validation schemas for the local LLM's JSON responses.

Kept separate from `app/worker/pipeline/types.py`'s plain dataclasses:
these are pydantic models whose only job is validating an untrusted LLM
response before it's trusted anywhere else in the pipeline.
"""

from pydantic import BaseModel, Field, field_validator


class ExtractionIngredientSchema(BaseModel):
    """One ingredient as returned by the recipe-extraction prompt.

    Attributes:
        raw_text: The ingredient line as the model read it (e.g. "2lbs
            chicken breast"), kept for display even if parsing below fails.
        name: The parsed ingredient name, used for the macro lookup.
        quantity: The parsed numeric quantity, if the model could extract one.
        unit: The parsed unit, if the model could extract one.
    """

    raw_text: str
    name: str
    quantity: float | None = None
    unit: str | None = None


class ExtractionSchema(BaseModel):
    """A structured recipe as returned by the recipe-extraction prompt.

    Attributes:
        name: The recipe's title.
        portion_count: How many portions the recipe makes.
        steps: The instruction steps, in order.
        ingredients: The recipe's ingredients.
        tags: Suggested tags.
    """

    name: str
    portion_count: int = Field(default=1, gt=0)
    steps: list[str] = Field(min_length=1)
    ingredients: list[ExtractionIngredientSchema] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)

    @field_validator("portion_count", mode="before")
    @classmethod
    def _default_missing_portion_count(cls, value: int | None) -> int:
        """Fall back to 1 portion when the model omits or nulls this field.

        Real model responses sometimes leave `portion_count` out or return
        `null` when the transcript never states a serving size — treating
        that as a hard failure would discard an otherwise-good extraction.
        """
        return value if value is not None else 1


class MacroEstimateSchema(BaseModel):
    """A per-100g macro estimate as returned by the macro-estimation prompt.

    Attributes:
        calories: Estimated calories per 100g.
        protein_g: Estimated protein (g) per 100g.
        carbs_g: Estimated carbohydrate (g) per 100g.
        fat_g: Estimated fat (g) per 100g.
    """

    calories: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
