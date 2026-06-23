from rest_framework import serializers

from content.models import (
    CheckBoxAnswerOption,
    CodingChallenge,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonTheory,
    RadioAnswerOption,
    TestCase,
)
from content.video_utils import build_video_payload


class EditorVideoMixin(serializers.Serializer):
    video = serializers.SerializerMethodField()

    def get_video(self, obj):
        return build_video_payload(obj, self.context.get("request"))


class EditorAnswerOptionSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = RadioAnswerOption
        fields = ("public_id", "text", "is_correct", "order_index")
        read_only_fields = ("order_index",)


class EditorCheckBoxAnswerOptionSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = CheckBoxAnswerOption
        fields = ("public_id", "text", "is_correct", "order_index")
        read_only_fields = ("order_index",)


class EditorTestCaseSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = TestCase
        fields = (
            "public_id",
            "input_data",
            "expected_output",
            "is_hidden",
            "order_index",
        )
        read_only_fields = ("order_index",)


class EditorTheorySerializer(EditorVideoMixin, serializers.ModelSerializer):
    module_public_id = serializers.UUIDField(
        source="module.public_id", read_only=True
    )

    class Meta:
        model = LessonTheory
        fields = (
            "public_id",
            "module_public_id",
            "title",
            "content",
            "comment",
            "video_url",
            "video_file",
            "video",
            "order_index",
            "is_active",
        )
        read_only_fields = ("public_id", "module_public_id", "video")


class EditorRadioSerializer(EditorVideoMixin, serializers.ModelSerializer):
    module_public_id = serializers.UUIDField(
        source="module.public_id", read_only=True
    )
    answer_options = EditorAnswerOptionSerializer(many=True, required=False)

    class Meta:
        model = LessonRadioQuestion
        fields = (
            "public_id",
            "module_public_id",
            "title",
            "question_text",
            "comment",
            "explanation",
            "solution_text",
            "video_url",
            "video_file",
            "video",
            "points",
            "order_index",
            "is_active",
            "answer_options",
        )
        read_only_fields = ("public_id", "module_public_id", "video")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["answer_options"] = EditorAnswerOptionSerializer(
            instance.answers.order_by("order_index"), many=True
        ).data
        return data

    def update(self, instance, validated_data):
        options = validated_data.pop("answer_options", None)
        instance = super().update(instance, validated_data)
        if options is not None:
            self._sync_radio_options(instance, options)
        return instance

    def _sync_radio_options(self, question, options_data):
        keep = []
        for i, row in enumerate(options_data, start=1):
            opt_id = row.get("public_id")
            if opt_id:
                opt = RadioAnswerOption.objects.filter(
                    public_id=opt_id, question=question
                ).first()
                if opt:
                    opt.text = row.get("text", opt.text)
                    opt.is_correct = row.get("is_correct", opt.is_correct)
                    opt.order_index = i
                    opt.save()
                    keep.append(opt.pk)
                    continue
            opt = RadioAnswerOption.objects.create(
                question=question,
                text=row.get("text", ""),
                is_correct=row.get("is_correct", False),
                order_index=i,
            )
            keep.append(opt.pk)
        question.answers.exclude(pk__in=keep).delete()


class EditorCheckboxSerializer(EditorVideoMixin, serializers.ModelSerializer):
    module_public_id = serializers.UUIDField(
        source="module.public_id", read_only=True
    )
    answer_options = EditorCheckBoxAnswerOptionSerializer(
        many=True, required=False
    )

    class Meta:
        model = LessonCheckBoxQuestion
        fields = (
            "public_id",
            "module_public_id",
            "title",
            "question_text",
            "comment",
            "explanation",
            "solution_text",
            "video_url",
            "video_file",
            "video",
            "points",
            "order_index",
            "is_active",
            "answer_options",
        )
        read_only_fields = ("public_id", "module_public_id", "video")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["answer_options"] = EditorCheckBoxAnswerOptionSerializer(
            instance.answers.order_by("order_index"), many=True
        ).data
        return data

    def update(self, instance, validated_data):
        options = validated_data.pop("answer_options", None)
        instance = super().update(instance, validated_data)
        if options is not None:
            self._sync_checkbox_options(instance, options)
        return instance

    def _sync_checkbox_options(self, question, options_data):
        keep = []
        for i, row in enumerate(options_data, start=1):
            opt_id = row.get("public_id")
            if opt_id:
                opt = CheckBoxAnswerOption.objects.filter(
                    public_id=opt_id, question=question
                ).first()
                if opt:
                    opt.text = row.get("text", opt.text)
                    opt.is_correct = row.get("is_correct", opt.is_correct)
                    opt.order_index = i
                    opt.save()
                    keep.append(opt.pk)
                    continue
            opt = CheckBoxAnswerOption.objects.create(
                question=question,
                text=row.get("text", ""),
                is_correct=row.get("is_correct", False),
                order_index=i,
            )
            keep.append(opt.pk)
        question.answers.exclude(pk__in=keep).delete()


class EditorCodingSerializer(EditorVideoMixin, serializers.ModelSerializer):
    module_public_id = serializers.UUIDField(
        source="module.public_id", read_only=True, allow_null=True
    )
    course_public_id = serializers.UUIDField(
        source="course.public_id", read_only=True, allow_null=True
    )
    test_cases = EditorTestCaseSerializer(many=True, required=False)

    class Meta:
        model = CodingChallenge
        fields = (
            "public_id",
            "module_public_id",
            "course_public_id",
            "title",
            "description",
            "instructions",
            "comment",
            "solution_text",
            "video_url",
            "video_file",
            "video",
            "initial_code",
            "solution_template",
            "difficulty",
            "points",
            "time_limit_ms",
            "memory_limit_mb",
            "order_index",
            "is_active",
            "test_cases",
        )
        read_only_fields = (
            "public_id",
            "module_public_id",
            "course_public_id",
            "video",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["test_cases"] = EditorTestCaseSerializer(
            instance.test_cases.order_by("order_index"), many=True
        ).data
        return data

    def update(self, instance, validated_data):
        tests = validated_data.pop("test_cases", None)
        instance = super().update(instance, validated_data)
        if tests is not None:
            self._sync_test_cases(instance, tests)
        return instance

    def _sync_test_cases(self, challenge, tests_data):
        keep = []
        for i, row in enumerate(tests_data, start=1):
            tc_id = row.get("public_id")
            if tc_id:
                tc = TestCase.objects.filter(
                    public_id=tc_id, challenge=challenge
                ).first()
                if tc:
                    tc.input_data = row.get("input_data", tc.input_data)
                    tc.expected_output = row.get(
                        "expected_output", tc.expected_output
                    )
                    tc.is_hidden = row.get("is_hidden", tc.is_hidden)
                    tc.order_index = i
                    tc.save()
                    keep.append(tc.pk)
                    continue
            tc = TestCase.objects.create(
                challenge=challenge,
                input_data=row.get("input_data", ""),
                expected_output=row.get("expected_output", ""),
                is_hidden=row.get("is_hidden", False),
                order_index=i,
            )
            keep.append(tc.pk)
        challenge.test_cases.exclude(pk__in=keep).delete()


EDITOR_SERIALIZERS = {
    "theory": EditorTheorySerializer,
    "radio": EditorRadioSerializer,
    "checkbox": EditorCheckboxSerializer,
    "coding": EditorCodingSerializer,
}
