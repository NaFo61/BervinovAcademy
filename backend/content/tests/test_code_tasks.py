import pytest

from content.models import CodeTask, CodeTaskTestCase, Course, Module


@pytest.mark.fast
@pytest.mark.unit
@pytest.mark.models
@pytest.mark.django_db
def test_code_task_defaults_and_str():
    course = Course.objects.create(title="Python", description="Basics")
    module = Module.objects.create(
        course=course, title="Intro", description="Start", order_index=1
    )

    code_task = CodeTask.objects.create(
        module=module,
        title="Sum numbers",
        task_text="Return sum of inputs",
        correct_code="print(sum(map(int, input().split())))",
        order_index=1,
    )

    assert code_task.submissions_count == 0
    assert code_task.solved_count == 0
    assert str(code_task) == "Intro - Sum numbers"


@pytest.mark.fast
@pytest.mark.unit
@pytest.mark.models
@pytest.mark.django_db
def test_code_task_test_case_relations():
    course = Course.objects.create(title="Python", description="Basics")
    module = Module.objects.create(
        course=course, title="Intro", description="Start", order_index=1
    )
    code_task = CodeTask.objects.create(
        module=module,
        title="Echo",
        task_text="Echo input",
        correct_code="print(input())",
        order_index=1,
    )

    test_case = CodeTaskTestCase.objects.create(
        code_task=code_task,
        input_data="hello",
        expected_output="hello",
        order_index=1,
    )

    assert code_task.tests.count() == 1
    assert code_task.tests.first() == test_case
    assert "Echo" in str(test_case)
