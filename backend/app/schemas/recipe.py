"""Request/response models for the recipe endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import MacroSource, RecipeStatus, RecipeVisibility


class IngredientWrite(BaseModel):
    """One ingredient, as submitted on create/update.

    Attributes:
        raw_text: The ingredient as originally extracted or typed.
        name: The parsed ingredient name.
        quantity: The parsed numeric quantity, if any.
        unit: The parsed unit, if any.
        calories: This ingredient's calories, if known.
        protein_g: This ingredient's protein in grams, if known.
        carbs_g: This ingredient's carbohydrate in grams, if known.
        fat_g: This ingredient's fat in grams, if known.
        macro_source: Whether these macros are USDA-verified or LLM-estimated.
    """

    raw_text: str
    name: str
    quantity: float | None = None
    unit: str | None = None
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    macro_source: MacroSource


class IngredientRead(IngredientWrite):
    """One ingredient, as returned in a recipe response.

    Attributes:
        id: The ingredient's primary key.
        sort_order: Preserves the ingredient list's original order.
    """

    id: uuid.UUID
    sort_order: int

    model_config = {"from_attributes": True}


class RecipeMacrosRead(BaseModel):
    """A recipe's aggregate per-portion macros.

    Attributes:
        portion_count: How many portions the recipe makes.
        calories_per_portion: Calories in one portion.
        protein_g_per_portion: Grams of protein in one portion.
        carbs_g_per_portion: Grams of carbohydrate in one portion.
        fat_g_per_portion: Grams of fat in one portion.
        macro_source: Whether these totals are USDA-verified, LLM-estimated,
            or a mix across ingredients.
    """

    portion_count: int
    calories_per_portion: float
    protein_g_per_portion: float
    carbs_g_per_portion: float
    fat_g_per_portion: float
    macro_source: MacroSource

    model_config = {"from_attributes": True}


class RecipeCreate(BaseModel):
    """Body of ``POST /api/v1/recipes``.

    Attributes:
        name: The recipe's title.
        source_url: The original video link.
        portion_count: How many portions the recipe makes.
        steps: The instruction steps, in order.
        ingredients: The recipe's ingredients.
        tags: Freeform tags; normalized (lowercased/trimmed) on write.
        visibility: Who besides the owner can see this recipe.
    """

    name: str
    source_url: str
    portion_count: int = Field(ge=1)
    steps: list[str]
    ingredients: list[IngredientWrite]
    tags: list[str] = []
    visibility: RecipeVisibility = RecipeVisibility.PERSONAL


class RecipeUpdate(BaseModel):
    """Body of ``PATCH /api/v1/recipes/{id}``.

    Any field left unset is unchanged; ``steps``/``ingredients``/``tags``,
    when provided, fully replace the recipe's existing list.

    Attributes:
        name: New title, if changing.
        portion_count: New portion count, if changing.
        steps: New instruction steps (full replacement), if changing.
        ingredients: New ingredients (full replacement), if changing —
            macros are recomputed from these.
        tags: New tags (full replacement), if changing.
    """

    name: str | None = None
    portion_count: int | None = Field(default=None, ge=1)
    steps: list[str] | None = None
    ingredients: list[IngredientWrite] | None = None
    tags: list[str] | None = None


class RecipeVisibilityUpdate(BaseModel):
    """Body of ``PATCH /api/v1/recipes/{id}/visibility``.

    Attributes:
        visibility: The recipe's new visibility.
    """

    visibility: RecipeVisibility


class StepRead(BaseModel):
    """One instruction step, as returned in a recipe response.

    Attributes:
        step_number: This step's position, 1-indexed.
        text: The instruction text.
    """

    step_number: int
    text: str

    model_config = {"from_attributes": True}


class RecipeRead(BaseModel):
    """Full representation of a recipe, as returned by the detail/list endpoints.

    Attributes:
        id: The recipe's primary key.
        owner_user_id: Whoever submitted the source link.
        household_id: The owner's household at creation time, if any.
        visibility: Who besides the owner can see this recipe.
        name: The recipe's title.
        source_url: The original video link.
        status: Where this submission is in the processing pipeline.
        failure_reason: A human-readable explanation, set only when
            ``status`` is failed.
        created_at: When the recipe was created.
        updated_at: When the recipe last changed.
        steps: The instruction steps, in order.
        ingredients: The recipe's ingredients, in order.
        macros: The recipe's aggregate macros, if computed.
        tags: The recipe's tags.
    """

    id: uuid.UUID
    owner_user_id: uuid.UUID
    household_id: uuid.UUID | None
    visibility: RecipeVisibility
    name: str
    source_url: str
    status: RecipeStatus
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime
    steps: list[StepRead]
    ingredients: list[IngredientRead]
    macros: RecipeMacrosRead | None
    tags: list[str]

    model_config = {"from_attributes": True}


class ShoppingListItemRead(BaseModel):
    """One deduplicated line on a recipe's shopping list.

    Attributes:
        name: The ingredient name.
        quantity: The parsed quantity, if any.
        unit: The parsed unit, if any.
        raw_text: The original extracted text.
    """

    name: str
    quantity: float | None
    unit: str | None
    raw_text: str

    model_config = {"from_attributes": True}
