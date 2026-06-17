import pytest

from content.models import CodingChallenge

pytest_plugins = (
    "content.tests.conftest",
    "users.tests.conftest",
)


@pytest.fixture(autouse=True)
def _disable_kafka_in_progress_tests(settings):
    """Без брокера тесты не должны ходить в сеть."""
    settings.KAFKA_BOOTSTRAP_SERVERS = ""
    from progress.kafka_publisher import reset_kafka_producer

    reset_kafka_producer()
    yield
    reset_kafka_producer()


@pytest.fixture(autouse=True)
def _seed_achievements(db):
    from progress.models import Achievement

    if Achievement.objects.exists():
        return
    defaults = [
        (
            "tasks_1",
            "tasks_solved",
            1,
            "Первый шаг",
            "Решил первую задачу",
            "👶",
            10,
        ),
        (
            "tasks_10",
            "tasks_solved",
            10,
            "Десятка",
            "10 решённых задач",
            "🔟",
            20,
        ),
        (
            "theories_10",
            "theories_read",
            10,
            "Книжный червь",
            "10 теорий",
            "📚",
            40,
        ),
    ]
    for (
        code,
        kind,
        threshold,
        title,
        description,
        emoji,
        order_index,
    ) in defaults:
        Achievement.objects.create(
            code=code,
            kind=kind,
            threshold=threshold,
            title=title,
            description=description,
            emoji=emoji,
            order_index=order_index,
        )


@pytest.fixture
def coding_challenge(db, module):
    return CodingChallenge.objects.create(
        module=module,
        course=module.course,
        title="Two Sum",
        description="Find pair",
        instructions="Return indices",
        initial_code="def solve(): pass",
        solution_template="pass",
        order_index=1,
        is_active=True,
    )
