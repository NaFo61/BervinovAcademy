# progress/serializers.py

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from content.models import (
    CheckBoxAnswerOption,
    CodingChallenge,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonTheory,
    RadioAnswerOption,
)

from .models import (
    CodeSubmission,
    UserAnswerCheckBox,
    UserAnswerRadio,
    UserLessonTheoryRead,
)


class UserAnswerRadioSerializer(serializers.ModelSerializer):
    """Сериализатор для ответов на radio-вопросы (несколько попыток на вопрос)."""

    question_title = serializers.CharField(
        source="question.title", read_only=True
    )
    selected_answer_text = serializers.CharField(
        source="selected_answer.text", read_only=True
    )
    solved_ever = serializers.SerializerMethodField()
    question = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=LessonRadioQuestion.objects.filter(is_active=True),
    )
    selected_answer = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=RadioAnswerOption.objects.all(),
    )

    class Meta:
        model = UserAnswerRadio
        fields = (
            "public_id",
            "question",
            "question_title",
            "selected_answer",
            "selected_answer_text",
            "is_correct",
            "points_earned",
            "solved_ever",
            "created_at",
        )
        read_only_fields = (
            "is_correct",
            "points_earned",
            "solved_ever",
            "created_at",
        )

    def get_solved_ever(self, obj: UserAnswerRadio) -> bool:
        ann = getattr(obj, "solved_ever", None)
        if ann is not None:
            return bool(ann)
        return UserAnswerRadio.objects.filter(
            user_id=obj.user_id,
            question_id=obj.question_id,
            is_correct=True,
        ).exists()

    def validate(self, attrs):
        question = attrs["question"]
        selected = attrs["selected_answer"]
        if selected.question_id != question.pk:
            raise serializers.ValidationError(
                {
                    "selected_answer": _(
                        "Вариант ответа не принадлежит выбранному вопросу"
                    )
                }
            )
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class UserAnswerCheckBoxSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ответов на checkbox-вопросы.

    ``selected_answers`` может быть пустым списком (пустой ответ).
    """

    question_title = serializers.CharField(
        source="question.title", read_only=True
    )
    selected_answers_text = serializers.SerializerMethodField()
    question = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=LessonCheckBoxQuestion.objects.filter(is_active=True),
    )
    selected_answers = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=CheckBoxAnswerOption.objects.all(),
        many=True,
        allow_empty=True,
    )

    class Meta:
        model = UserAnswerCheckBox
        fields = (
            "public_id",
            "question",
            "question_title",
            "selected_answers",
            "selected_answers_text",
            "is_correct",
            "points_earned",
            "created_at",
        )
        read_only_fields = ("is_correct", "points_earned", "created_at")

    def validate(self, attrs):
        question = attrs["question"]
        for opt in attrs.get("selected_answers", []):
            if opt.question_id != question.pk:
                raise serializers.ValidationError(
                    {
                        "selected_answers": _(
                            "Один из вариантов не принадлежит выбранному вопросу"
                        )
                    }
                )
        return attrs

    def get_selected_answers_text(self, obj):
        return [a.text for a in obj.selected_answers.all()]

    def create(self, validated_data):
        selected_answers = validated_data.pop("selected_answers", [])
        validated_data["user"] = self.context["request"].user
        instance = super().create(validated_data)
        if selected_answers:
            instance.selected_answers.set(selected_answers)
        instance.is_correct = instance.calculate_correctness()
        instance.points_earned = instance.calculate_points()
        instance.save(
            update_fields=["is_correct", "points_earned", "updated_at"]
        )
        return instance

    def submit(self, validated_data):
        """
        Сохраняет ответ только при полной правильности.
        При ошибке возвращает dict с результатом проверки без записи в БД.
        """
        user = self.context["request"].user
        question = validated_data["question"]
        selected_answers = list(validated_data.get("selected_answers", []))

        correct_set = set(question.answers.filter(is_correct=True))
        selected_set = set(selected_answers)
        is_correct = bool(correct_set) and selected_set == correct_set

        base = {
            "question": str(question.public_id),
            "question_title": question.title,
            "selected_answers": [str(a.public_id) for a in selected_answers],
            "selected_answers_text": [a.text for a in selected_answers],
            "is_correct": is_correct,
            "points_earned": question.points if is_correct else 0,
            "saved": is_correct,
        }

        if not is_correct:
            return None, base

        instance, _created = UserAnswerCheckBox.objects.get_or_create(
            user=user,
            question=question,
        )
        instance.selected_answers.set(selected_answers)
        instance.is_correct = True
        instance.points_earned = question.points
        instance.save(
            update_fields=["is_correct", "points_earned", "updated_at"]
        )
        out = UserAnswerCheckBoxSerializer(instance, context=self.context).data
        out["saved"] = True
        return instance, out


class UserLessonTheoryReadSerializer(serializers.ModelSerializer):
    lesson = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=LessonTheory.objects.filter(is_active=True),
    )
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = UserLessonTheoryRead
        fields = ("public_id", "lesson", "lesson_title", "read_at")
        read_only_fields = ("public_id", "lesson_title", "read_at")


class CodeSubmissionSerializer(serializers.ModelSerializer):
    """Чтение сохранённой отправки кода (в т.ч. после ``POST …/progress/code/``)."""

    challenge_title = serializers.CharField(
        source="challenge.title", read_only=True
    )
    challenge_public_id = serializers.UUIDField(
        source="challenge.public_id",
        read_only=True,
    )
    failed_test_number = serializers.SerializerMethodField()
    actual_output = serializers.SerializerMethodField()
    expected_output = serializers.SerializerMethodField()

    class Meta:
        model = CodeSubmission
        fields = (
            "public_id",
            "challenge_public_id",
            "challenge_title",
            "code",
            "status",
            "tests_passed",
            "total_tests",
            "error_message",
            "failed_test_number",
            "actual_output",
            "expected_output",
            "submitted_at",
            "completed_at",
        )
        read_only_fields = (
            "public_id",
            "challenge_public_id",
            "challenge_title",
            "status",
            "tests_passed",
            "total_tests",
            "error_message",
            "failed_test_number",
            "actual_output",
            "expected_output",
            "submitted_at",
            "completed_at",
        )

    @staticmethod
    def _feedback_dict(obj: CodeSubmission) -> dict:
        raw = obj.test_results
        return raw if isinstance(raw, dict) else {}

    def get_failed_test_number(self, obj: CodeSubmission):
        n = self._feedback_dict(obj).get("failed_test_number")
        return n if isinstance(n, int) else None

    def get_actual_output(self, obj: CodeSubmission):
        v = self._feedback_dict(obj).get("actual_output")
        if v is None:
            return None
        return v if isinstance(v, str) else str(v)

    def get_expected_output(self, obj: CodeSubmission):
        v = self._feedback_dict(obj).get("expected_output")
        if v is None:
            return None
        return v if isinstance(v, str) else str(v)


class CodeSubmissionCreateSerializer(serializers.ModelSerializer):
    """
    Тело запроса при отправке кода: активная задача по public_id и текст решения.

    Пример JSON::

        {"challenge": "550e8400-e29b-41d4-a716-446655440000", "code": "print(1)"}

    Поле ``challenge`` — UUID задачи (тот же ``public_id``, что в URL
    ``/api/content/challenges/{public_id}/``). Отправка:
    ``POST /api/progress/code/``.
    """

    challenge = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=CodingChallenge.objects.filter(is_active=True),
    )
    exam_attempt = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=CodeSubmission.objects.none(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = CodeSubmission
        fields = ("challenge", "code", "exam_attempt")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from exams.models import ExamAttempt

        self.fields["exam_attempt"].queryset = ExamAttempt.objects.filter(
            status=ExamAttempt.Status.IN_PROGRESS,
        )

    def validate(self, attrs):
        attempt = attrs.get("exam_attempt")
        if attempt and attempt.user_id != self.context["request"].user.id:
            raise serializers.ValidationError(
                {"exam_attempt": _("Недопустимая попытка КР.")}
            )
        challenge = attrs.get("challenge")
        if attempt and challenge and challenge.exam_id != attempt.exam_id:
            raise serializers.ValidationError(
                {"challenge": _("Задача не относится к этой контрольной.")}
            )
        return attrs

    def validate_code(self, value: str) -> str:
        text = (value or "").strip()
        if not text:
            raise serializers.ValidationError(_("Код не может быть пустым"))
        return text

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return CodeSubmission.objects.create(
            status="pending", **validated_data
        )
