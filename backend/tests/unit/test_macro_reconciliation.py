import pytest

from app.core.enums import MacroSource
from app.core.macro_reconciliation import compute_recipe_macros, reconcile_macro_source
from app.db.models.ingredient import Ingredient


def make_ingredient(
    *,
    calories: float | None,
    protein_g: float | None,
    carbs_g: float | None,
    fat_g: float | None,
    macro_source: MacroSource,
) -> Ingredient:
    return Ingredient(
        raw_text="test",
        name="test",
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        macro_source=macro_source,
        sort_order=0,
    )


class TestReconcileMacroSource:
    def test_all_verified_is_verified(self) -> None:
        result = reconcile_macro_source([MacroSource.USDA_VERIFIED, MacroSource.USDA_VERIFIED])
        assert result == MacroSource.USDA_VERIFIED

    def test_all_estimated_is_estimated(self) -> None:
        result = reconcile_macro_source([MacroSource.LLM_ESTIMATED, MacroSource.LLM_ESTIMATED])
        assert result == MacroSource.LLM_ESTIMATED

    def test_mix_of_verified_and_estimated_is_mixed(self) -> None:
        result = reconcile_macro_source([MacroSource.USDA_VERIFIED, MacroSource.LLM_ESTIMATED])
        assert result == MacroSource.MIXED

    def test_empty_list_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            reconcile_macro_source([])


class TestComputeRecipeMacros:
    def test_sums_and_divides_by_portion_count(self) -> None:
        ingredients = [
            make_ingredient(
                calories=200,
                protein_g=20,
                carbs_g=10,
                fat_g=5,
                macro_source=MacroSource.USDA_VERIFIED,
            ),
            make_ingredient(
                calories=200,
                protein_g=20,
                carbs_g=10,
                fat_g=5,
                macro_source=MacroSource.USDA_VERIFIED,
            ),
        ]

        totals = compute_recipe_macros(ingredients, portion_count=2)

        assert totals.calories_per_portion == 200
        assert totals.protein_g_per_portion == 20
        assert totals.carbs_g_per_portion == 10
        assert totals.fat_g_per_portion == 5
        assert totals.macro_source == MacroSource.USDA_VERIFIED

    def test_missing_macro_values_contribute_zero(self) -> None:
        ingredients = [
            make_ingredient(
                calories=100,
                protein_g=None,
                carbs_g=None,
                fat_g=None,
                macro_source=MacroSource.LLM_ESTIMATED,
            ),
        ]

        totals = compute_recipe_macros(ingredients, portion_count=1)

        assert totals.calories_per_portion == 100
        assert totals.protein_g_per_portion == 0
        assert totals.carbs_g_per_portion == 0
        assert totals.fat_g_per_portion == 0

    def test_reflects_mixed_macro_sources(self) -> None:
        ingredients = [
            make_ingredient(
                calories=100,
                protein_g=10,
                carbs_g=5,
                fat_g=2,
                macro_source=MacroSource.USDA_VERIFIED,
            ),
            make_ingredient(
                calories=100,
                protein_g=10,
                carbs_g=5,
                fat_g=2,
                macro_source=MacroSource.LLM_ESTIMATED,
            ),
        ]

        totals = compute_recipe_macros(ingredients, portion_count=1)

        assert totals.macro_source == MacroSource.MIXED

    def test_empty_ingredients_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            compute_recipe_macros([], portion_count=1)

    def test_portion_count_below_one_raises(self) -> None:
        ingredients = [
            make_ingredient(
                calories=100,
                protein_g=10,
                carbs_g=5,
                fat_g=2,
                macro_source=MacroSource.USDA_VERIFIED,
            )
        ]
        with pytest.raises(ValueError, match="portion_count"):
            compute_recipe_macros(ingredients, portion_count=0)
