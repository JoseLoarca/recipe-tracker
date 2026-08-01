"""Building a recipe's shopping list from its ingredients."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


class IngredientLike(Protocol):
    """The subset of `app.db.models.ingredient.Ingredient` this module needs.

    A `Protocol` rather than importing the ORM model directly, so this
    module stays framework-agnostic and easy to unit test with plain objects.
    """

    name: str
    quantity: float | None
    unit: str | None
    raw_text: str


@dataclass(frozen=True)
class ShoppingListItem:
    """One deduplicated line on a recipe's shopping list.

    Attributes:
        name: The ingredient name.
        quantity: The parsed quantity, if any.
        unit: The parsed unit, if any.
        raw_text: The original extracted text, for display when
            quantity/unit weren't parseable.
    """

    name: str
    quantity: float | None
    unit: str | None
    raw_text: str


def build_shopping_list(ingredients: Sequence[IngredientLike]) -> list[ShoppingListItem]:
    """Build a deduplicated shopping list from a recipe's ingredients.

    Ingredients are deduplicated by their normalized (lowercased, trimmed)
    name, keeping the first occurrence and preserving the ingredient list's
    original order.

    Args:
        ingredients: The recipe's ingredients, in their stored order.

    Returns:
        One `ShoppingListItem` per distinct ingredient name.
    """
    seen: set[str] = set()
    items: list[ShoppingListItem] = []
    for ingredient in ingredients:
        key = ingredient.name.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(
            ShoppingListItem(
                name=ingredient.name,
                quantity=ingredient.quantity,
                unit=ingredient.unit,
                raw_text=ingredient.raw_text,
            )
        )
    return items
