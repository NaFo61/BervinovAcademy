# progress/serializers.py (новый файл)

from rest_framework import serializers

from .models import CodeSubmission, UserAnswerCheckBox, UserAnswerRadio


class UserAnswerRadioSerializer(serializers.ModelSerializer):
    """Сериализатор для ответов на radio-вопросы"""

    question_title = serializers.CharField(
        source="question.title", read_only=True
    )
    selected_answer_text = serializers.CharField(
        source="selected_answer.text", read_only=True
    )

    class Meta:
        model = UserAnswerRadio
        fields = (
            "id",
            "question",
            "question_title",
            "selected_answer",
            "selected_answer_text",
            "is_correct",
            "points_earned",
            "created_at",
        )
        read_only_fields = ("is_correct", "points_earned", "created_at")

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class UserAnswerCheckBoxSerializer(serializers.ModelSerializer):
    """Сериализатор для ответов на checkbox-вопросы"""

    question_title = serializers.CharField(
        source="question.title", read_only=True
    )
    selected_answers_text = serializers.SerializerMethodField()

    class Meta:
        model = UserAnswerCheckBox
        fields = (
            "id",
            "question",
            "question_title",
            "selected_answers",
            "selected_answers_text",
            "is_correct",
            "points_earned",
            "created_at",
        )
        read_only_fields = ("is_correct", "points_earned", "created_at")

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
            instance.save()

        return instance


class CodeSubmissionSerializer(serializers.ModelSerializer):
    """Сериализатор для отправок решений"""

    challenge_title = serializers.CharField(
        source="challenge.title", read_only=True
    )

    class Meta:
        model = CodeSubmission
        fields = (
            "submission_id",
            "challenge",
            "challenge_title",
            "code",
            "status",
            "tests_passed",
            "total_tests",
            "error_message",
            "submitted_at",
            "completed_at",
        )
        read_only_fields = (
            "submission_id",
            "status",
            "tests_passed",
            "total_tests",
            "error_message",
            "submitted_at",
            "completed_at",
        )

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
