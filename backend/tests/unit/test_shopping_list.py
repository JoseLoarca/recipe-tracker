from app.core.enums import MacroSource
from app.core.shopping_list import build_shopping_list
from app.db.models.ingredient import Ingredient


def make_ingredient(
    *,
    name: str,
    quantity: float | None = 1.0,
    unit: str | None = "cup",
    raw_text: str | None = None,
) -> Ingredient:
    return Ingredient(
        raw_text=raw_text or f"{quantity} {unit} {name}",
        name=name,
        quantity=quantity,
        unit=unit,
        macro_source=MacroSource.USDA_VERIFIED,
        sort_order=0,
    )


def test_build_shopping_list_preserves_order() -> None:
    ingredients = [
        make_ingredient(name="chicken breast"),
        make_ingredient(name="quinoa"),
        make_ingredient(name="frozen vegetables"),
    ]

    items = build_shopping_list(ingredients)

    assert [item.name for item in items] == ["chicken breast", "quinoa", "frozen vegetables"]


def test_build_shopping_list_dedupes_by_normalized_name() -> None:
    ingredients = [
        make_ingredient(name="Salt"),
        make_ingredient(name="pepper"),
        make_ingredient(name=" salt "),
    ]

    items = build_shopping_list(ingredients)

    assert [item.name for item in items] == ["Salt", "pepper"]


def test_build_shopping_list_handles_empty_input() -> None:
    assert build_shopping_list([]) == []
