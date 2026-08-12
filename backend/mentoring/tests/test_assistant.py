"""Unit-тесты ИИ-помощника: шаблоны и mock urlopen."""

import json
from unittest.mock import MagicMock, patch

import pytest

from mentoring.assistant import (
    build_system_prompt,
    generate_assistant_reply,
    render_prompt_template,
    resolve_prompt_template,
)
from mentoring.models import AssistantSettings


def test_render_known_and_unknown_placeholders():
    text = render_prompt_template(
        "A={{condition}}; B={{unknown}}; C={{title}}",
        {"condition": "сумма", "title": "Задача 1"},
    )
    assert text == "A=сумма; B=; C=Задача 1"


@pytest.mark.django_db
def test_resolve_falls_back_to_default_without_db_row():
    from mentoring.models import DEFAULT_ASSISTANT_BASE_PROMPT

    AssistantSettings.objects.all().delete()
    template = resolve_prompt_template({"lesson_kind": "theory"})
    assert template == DEFAULT_ASSISTANT_BASE_PROMPT


@pytest.mark.django_db
def test_base_prompt_used_when_no_override(db):
    from content.models import CodingChallenge, Course, Module, Technology
    from users.models import User

    AssistantSettings.objects.filter(pk=1).delete()
    AssistantSettings.objects.create(
        pk=1, base_prompt="BASE {{condition}} {{title}}"
    )
    mentor = User.objects.create_user(
        email="prompt-mentor@academy.com",
        phone="+79001110001",
        password="password",
        role="mentor",
    )
    tech = Technology.objects.create(name="Py Prompt")
    course = Course.objects.create(
        title="Курс Промпт",
        description="d",
        slug="prompt-course",
        is_active=True,
        mentor=mentor,
    )
    course.technology.add(tech)
    module = Module.objects.create(
        course=course, title="M1", description="d", is_active=True
    )
    ch = CodingChallenge.objects.create(
        title="Сумма",
        description="Считай два числа",
        instructions="Выведи сумму",
        solution_template="",
        module=module,
        course=course,
        assistant_prompt="",
    )
    prompt = build_system_prompt(
        {
            "lesson_kind": "coding",
            "lesson_public_id": str(ch.public_id),
        }
    )
    assert prompt.startswith("BASE ")
    assert "Считай два числа" in prompt
    assert "Сумма" in prompt


@pytest.mark.django_db
def test_challenge_override_beats_base(db):
    from content.models import (
        CodingChallenge,
        Course,
        Module,
        Technology,
        TestCase,
    )
    from users.models import User

    AssistantSettings.objects.filter(pk=1).delete()
    AssistantSettings.objects.create(pk=1, base_prompt="BASE {{condition}}")
    mentor = User.objects.create_user(
        email="prompt-mentor2@academy.com",
        phone="+79001110002",
        password="password",
        role="mentor",
    )
    tech = Technology.objects.create(name="Py Prompt 2")
    course = Course.objects.create(
        title="Курс 2",
        description="d",
        slug="prompt-course-2",
        is_active=True,
        mentor=mentor,
    )
    course.technology.add(tech)
    module = Module.objects.create(
        course=course,
        title="M1",
        description="d",
        is_active=True,
        assistant_prompt="MODULE {{module}}",
    )
    ch = CodingChallenge.objects.create(
        title="Особая",
        description="Условие А",
        instructions="",
        solution_template="",
        module=module,
        course=course,
        assistant_prompt="TASK {{tests}} :: {{condition}}",
    )
    TestCase.objects.create(
        challenge=ch,
        input_data="1 2",
        expected_output="3",
        is_hidden=False,
        order_index=1,
    )
    TestCase.objects.create(
        challenge=ch,
        input_data="secret",
        expected_output="x",
        is_hidden=True,
        order_index=2,
    )
    prompt = build_system_prompt(
        {
            "lesson_kind": "coding",
            "lesson_public_id": str(ch.public_id),
            "user_code": "print(1)",
        }
    )
    assert "BASE " in prompt
    assert "MODULE M1" in prompt
    assert "TASK " in prompt
    assert "Условие А" in prompt
    assert "1 2" in prompt
    assert "secret" not in prompt


@pytest.mark.django_db
def test_module_prompt_without_task_prompt(db):
    from content.models import CodingChallenge, Course, Module, Technology
    from users.models import User

    AssistantSettings.objects.filter(pk=1).delete()
    AssistantSettings.objects.create(pk=1, base_prompt="BASE")
    mentor = User.objects.create_user(
        email="prompt-mentor3@academy.com",
        phone="+79001110003",
        password="password",
        role="mentor",
    )
    tech = Technology.objects.create(name="Py Prompt 3")
    course = Course.objects.create(
        title="Курс 3",
        description="d",
        slug="prompt-course-3",
        is_active=True,
        mentor=mentor,
    )
    course.technology.add(tech)
    module = Module.objects.create(
        course=course,
        title="Циклы",
        description="d",
        is_active=True,
        assistant_prompt="Для модуля циклов не давай готовый for.",
    )
    ch = CodingChallenge.objects.create(
        title="Сумма",
        description="Условие",
        instructions="",
        solution_template="",
        module=module,
        course=course,
        assistant_prompt="",
    )
    prompt = build_system_prompt(
        {
            "lesson_kind": "coding",
            "lesson_public_id": str(ch.public_id),
        }
    )
    assert "BASE" in prompt
    assert "не давай готовый for" in prompt
    assert prompt.index("BASE") < prompt.index("не давай готовый for")


def test_llm_reply_via_openai_compatible(settings):
    settings.ASSISTANT_LLM_ENABLED = True
    settings.OPENAI_API_KEY = "test-gemini-key"
    settings.OPENAI_BASE_URL = (
        "https://generativelanguage.googleapis.com/v1beta/openai"
    )
    settings.OPENAI_MODEL = "gemini-2.0-flash"

    payload = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Начните с чтения двух чисел.",
                }
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False

    with patch(
        "mentoring.assistant.urllib.request.urlopen",
        return_value=mock_resp,
    ) as urlopen_mock:
        result = generate_assistant_reply(
            message="С чего начать?",
            history=[],
            context={
                "course_title": "ЕГЭ",
                "lesson_kind": "coding",
                "lesson_title": "Сумма чисел",
                "lesson_statement": "Считайте два числа и выведите сумму.",
            },
        )

    assert result["mode"] == "llm"
    assert result["model"] == "gemini-2.0-flash"
    assert "двух чисел" in result["reply"]
    urlopen_mock.assert_called_once()
    req = urlopen_mock.call_args[0][0]
    body = json.loads(req.data.decode("utf-8"))
    system = body["messages"][0]["content"]
    assert "Сумма чисел" in system or "Считайте два числа" in system
