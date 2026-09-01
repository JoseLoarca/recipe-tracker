import logging

from app.worker.logging_context import PipelineContextFilter, bind_pipeline_context


def make_record() -> logging.LogRecord:
    return logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hi",
        args=(),
        exc_info=None,
    )


class TestPipelineContextFilter:
    def test_defaults_to_none_outside_a_bound_context(self) -> None:
        record = make_record()
        PipelineContextFilter().filter(record)
        assert record.correlation_id is None
        assert record.recipe_id is None

    def test_attaches_ids_inside_a_bound_context(self) -> None:
        with bind_pipeline_context(correlation_id="corr-1", recipe_id="recipe-1"):
            record = make_record()
            PipelineContextFilter().filter(record)
        assert record.correlation_id == "corr-1"
        assert record.recipe_id == "recipe-1"

    def test_resets_after_the_context_exits(self) -> None:
        with bind_pipeline_context(correlation_id="corr-1", recipe_id="recipe-1"):
            pass
        record = make_record()
        PipelineContextFilter().filter(record)
        assert record.correlation_id is None
        assert record.recipe_id is None

    def test_never_drops_a_record(self) -> None:
        assert PipelineContextFilter().filter(make_record()) is True
