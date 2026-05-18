from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action, display

from content.models import (
    CheckBoxAnswerOption,
    CodingChallenge,
    Course,
    LessonCheckBoxQuestion,
    LessonRadioQuestion,
    LessonTheory,
    Module,
    RadioAnswerOption,
    Technology,
    TestCase,
)


def _open_link(url):
    return format_html(
        '<a href="{}" style="color: #0d6efd;" title="{}">→</a>',
        url,
        _("Открыть"),
    )


def _lesson_counts_for_module(module):
    return (
        module.lessons_theories.count(),
        module.lessons_radio_questions.count(),
        module.lessons_checkbox_questions.count(),
    )


def _format_lesson_counts(theory, radio, checkbox):
    total = theory + radio + checkbox
    if total == 0:
        return format_html('<span style="color: #dc3545;">0</span>')
    parts = []
    if theory:
        parts.append(f"{theory} {_('теор.')}")
    if radio:
        parts.append(f"{radio} radio")
    if checkbox:
        parts.append(f"{checkbox} {_('чекб.')}")
    return format_html("{}", " · ".join(parts))


def _clone_course(original):
    base_slug = f"{original.slug}-copy"
    slug = base_slug
    counter = 1
    while Course.objects.filter(slug=slug).exists():
        counter += 1
        slug = f"{base_slug}-{counter}"

    new_course = Course.objects.create(
        title=f"{original.title} ({_('Копия')})",
        slug=slug,
        description=original.description,
        image=original.image,
        is_active=False,
    )
    new_course.technology.set(original.technology.all())

    for module in original.modules.order_by("order_index"):
        new_module = Module.objects.create(
            course=new_course,
            title=module.title,
            description=module.description,
            is_active=module.is_active,
        )

        for lesson in module.lessons_theories.order_by("order_index"):
            LessonTheory.objects.create(
                module=new_module,
                title=lesson.title,
                content=lesson.content,
                is_active=lesson.is_active,
            )

        for question in module.lessons_radio_questions.order_by("order_index"):
            new_question = LessonRadioQuestion.objects.create(
                module=new_module,
                title=question.title,
                question_text=question.question_text,
                explanation=question.explanation,
                points=question.points,
                is_active=question.is_active,
            )
            for answer in question.answers.order_by("order_index"):
                RadioAnswerOption.objects.create(
                    question=new_question,
                    text=answer.text,
                    is_correct=answer.is_correct,
                )

        for question in module.lessons_checkbox_questions.order_by(
            "order_index"
        ):
            new_question = LessonCheckBoxQuestion.objects.create(
                module=new_module,
                title=question.title,
                question_text=question.question_text,
                explanation=question.explanation,
                points=question.points,
                is_active=question.is_active,
            )
            for answer in question.answers.order_by("order_index"):
                CheckBoxAnswerOption.objects.create(
                    question=new_question,
                    text=answer.text,
                    is_correct=answer.is_correct,
                )

        for challenge in module.challenges.order_by("order_index"):
            new_challenge = CodingChallenge.objects.create(
                course=new_course,
                module=new_module,
                title=challenge.title,
                description=challenge.description,
                instructions=challenge.instructions,
                difficulty=challenge.difficulty,
                points=challenge.points,
                initial_code=challenge.initial_code,
                solution_template=challenge.solution_template,
                time_limit_ms=challenge.time_limit_ms,
                memory_limit_mb=challenge.memory_limit_mb,
                is_active=challenge.is_active,
            )
            for test_case in challenge.test_cases.order_by("order_index"):
                TestCase.objects.create(
                    challenge=new_challenge,
                    input_data=test_case.input_data,
                    expected_output=test_case.expected_output,
                    is_hidden=test_case.is_hidden,
                )

    return new_course


@admin.register(Technology)
class TechnologyAdmin(ModelAdmin):
    list_display = ("name", "courses_count", "is_used")
    search_fields = ("name",)
    list_per_page = 20
    ordering = ("name",)
    icon = "science"

    @admin.display(
        description=_("Количество курсов"), ordering="courses_count"
    )
    def courses_count(self, obj):
        count = obj.courses.count()
        url = (
            reverse("admin:content_course_changelist")
            + f"?technology__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{}</a>', url, count)

    @admin.display(description=_("Используется"), boolean=True)
    def is_used(self, obj):
        return obj.courses.exists()


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    """Админка для курсов"""

    list_display = (
        "title",
        "technologies_list",
        "modules_count",
        "is_active",
        "created_at",
        "actions_column",
    )
    list_filter = (
        "is_active",
        "technology",
        "created_at",
    )
    search_fields = ("title", "description", "technology__name")
    list_per_page = 20
    ordering = ("-created_at",)
    filter_horizontal = ("technology",)
    readonly_fields = ("created_at", "courses_stats")
    prepopulated_fields = {"slug": ("title",)}
    icon = "school"

    fieldsets = (
        (
            _("Основная информация"),
            {
                "fields": (
                    "title",
                    "slug",
                    "description",
                    "image",
                    "technology",
                    "is_active",
                ),
            },
        ),
        (
            _("Статистика"),
            {
                "fields": ("courses_stats",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Даты"),
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Технологии"))
    def technologies_list(self, obj):
        technologies = obj.technology.all()
        if not technologies:
            return "—"

        tech_links = []
        for tech in technologies[:3]:
            url = reverse("admin:content_technology_change", args=[tech.id])
            tech_links.append(f'<a href="{url}">{tech.name}</a>')

        result = ", ".join(tech_links)
        if technologies.count() > 3:
            result += (
                '<span style="color: #666;">('
                f"+{technologies.count() - 3})</span>"
            )

        return format_html(result)

    @admin.display(description=_("Модули"))
    def modules_count(self, obj):
        count = obj.modules.count()
        if count == 0:
            return format_html(
                '<span style="color: #dc3545;">{}</span>', count
            )

        url = (
            reverse("admin:content_module_changelist")
            + f"?course__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{}</a>', url, count)

    @admin.display(description=_("Статистика"))
    def courses_stats(self, obj):
        modules = obj.modules.count()
        theory = LessonTheory.objects.filter(module__course=obj).count()
        radio = LessonRadioQuestion.objects.filter(module__course=obj).count()
        checkbox = LessonCheckBoxQuestion.objects.filter(
            module__course=obj
        ).count()
        total_lessons = theory + radio + checkbox

        stats_html = f"""
        <div style="
            padding: 0.75rem;
            background: var(--primary-bg);
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 0.875rem;
        ">
            <div style="margin-bottom: 0.25rem;">
                <strong style="color: var(--primary-text);">
                {_('Модули')}:
                </strong>
                <span style="color: var(--secondary-text);">
                {modules}
                </span>
            </div>
            <div>
                <strong style="color: var(--primary-text);">
                {_('Уроки (всего)')}:
                </strong>
                <span style="color: var(--secondary-text);">
                {total_lessons}
                </span>
            </div>
            <div style="font-size: 0.8125rem; color: var(--secondary-text);">
                {_('Теория')}: {theory} · radio:
                 {radio} · {_('чекб.')}: {checkbox}
            </div>
        </div>
        """
        return format_html(stats_html)

    @display(description=_("Действия"), label=True)
    def actions_column(self, obj):
        return _open_link(
            reverse("admin:content_course_change", args=[obj.id])
        )

    @action(description=_("Активировать курсы ✅"), permissions=["change"])
    def activate_courses(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f"{updated} курсов активировано ✅"),
            messages.SUCCESS,
        )

    @action(description=_("Деактивировать курсы ❌"), permissions=["change"])
    def deactivate_courses(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f"{updated} курсов деактивировано ❌"),
            messages.WARNING,
        )

    @action(description=_("Клонировать курс"), permissions=["add"])
    def clone_course(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(
                request,
                _("Выберите только один курс для клонирования"),
                messages.ERROR,
            )
            return

        original = queryset.prefetch_related(
            "technology",
            "modules__lessons_theories",
            "modules__lessons_radio_questions__answers",
            "modules__lessons_checkbox_questions__answers",
            "modules__challenges__test_cases",
        ).first()
        new_course = _clone_course(original)

        self.message_user(
            request,
            _("Курс «%(title)s» успешно клонирован с модулями и уроками")
            % {"title": new_course.title},
            messages.SUCCESS,
        )

    actions = ["activate_courses", "deactivate_courses", "clone_course"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("technology", "modules")


class ModuleInline(TabularInline):
    """Модули курса на странице редактирования курса"""

    model = Module
    extra = 0
    ordering = ("order_index",)
    ordering_field = "order_index"
    hide_ordering_field = True
    show_change_link = True
    fields = ("title", "is_active", "lessons_inline_count")
    readonly_fields = ("lessons_inline_count",)

    @admin.display(description=_("Уроки"))
    def lessons_inline_count(self, obj):
        if not obj.pk:
            return "—"
        theory, radio, checkbox = _lesson_counts_for_module(obj)
        return _format_lesson_counts(theory, radio, checkbox)


CourseAdmin.inlines = [ModuleInline]


class LessonTheoryInline(TabularInline):
    """Инлайн для теоретических уроков"""

    model = LessonTheory
    extra = 1
    ordering = ("order_index",)
    ordering_field = "order_index"
    hide_ordering_field = True
    show_change_link = True

    fields = ("title", "content_preview", "is_active")
    readonly_fields = ("content_preview",)

    @admin.display(description=_("Содержание"))
    def content_preview(self, obj):
        if not obj.content:
            return "—"
        preview = (
            obj.content[:100] + "..."
            if len(obj.content) > 100
            else obj.content
        )
        return format_html('<span title="{}">{}</span>', obj.content, preview)


class LessonRadioQuestionInline(TabularInline):
    """Инлайн для радио-вопросов в модуле"""

    model = LessonRadioQuestion
    extra = 1
    ordering = ("order_index",)
    ordering_field = "order_index"
    hide_ordering_field = True
    show_change_link = True
    fields = (
        "title",
        "question_preview",
        "points",
        "is_active",
    )
    readonly_fields = ("question_preview",)

    @admin.display(description=_("Вопрос"))
    def question_preview(self, obj):
        if not obj.question_text:
            return "—"
        preview = (
            obj.question_text[:100] + "..."
            if len(obj.question_text) > 100
            else obj.question_text
        )
        return format_html(
            '<span title="{}">{}</span>', obj.question_text, preview
        )


class LessonCheckBoxQuestionInline(TabularInline):
    """Инлайн для чекбокс-вопросов в модуле"""

    model = LessonCheckBoxQuestion
    extra = 1
    ordering = ("order_index",)
    ordering_field = "order_index"
    hide_ordering_field = True
    show_change_link = True
    fields = (
        "title",
        "question_preview",
        "points",
        "is_active",
    )
    readonly_fields = ("question_preview",)

    @admin.display(description=_("Вопрос"))
    def question_preview(self, obj):
        if not obj.question_text:
            return "—"
        preview = (
            obj.question_text[:100] + "..."
            if len(obj.question_text) > 100
            else obj.question_text
        )
        return format_html(
            '<span title="{}">{}</span>', obj.question_text, preview
        )


class CodingChallengeInline(TabularInline):
    """Задачи по программированию в модуле"""

    model = CodingChallenge
    fk_name = "module"
    extra = 0
    ordering = ("order_index",)
    ordering_field = "order_index"
    hide_ordering_field = True
    show_change_link = True
    fields = ("title", "difficulty", "points", "is_active")

    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        if obj.module_id and not obj.course_id:
            obj.course_id = obj.module.course_id
        if commit:
            obj.save()
            form.save_m2m()
        return obj


@admin.register(Module)
class ModuleAdmin(ModelAdmin):
    """Админка для модулей"""

    list_display = (
        "title",
        "course_link",
        "lessons_count",
        "is_active",
        "actions_column",
    )
    list_filter = (
        "is_active",
        "course",
    )
    search_fields = ("title", "description", "course__title")
    list_per_page = 20
    ordering = ("course", "order_index")
    readonly_fields = ("lessons_count_display",)
    icon = "list_alt"

    inlines = [
        LessonTheoryInline,
        LessonRadioQuestionInline,
        LessonCheckBoxQuestionInline,
        CodingChallengeInline,
    ]

    fieldsets = (
        (
            _("Основная информация"),
            {
                "fields": (
                    "course",
                    "title",
                    "description",
                    "is_active",
                ),
            },
        ),
        (
            _("Статистика"),
            {
                "fields": ("lessons_count_display",),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Курс"), ordering="course__title")
    def course_link(self, obj):
        url = reverse("admin:content_course_change", args=[obj.course.id])
        return format_html('<a href="{}">{}</a>', url, obj.course.title)

    @admin.display(description=_("Уроки"))
    def lessons_count(self, obj):
        theory, radio, checkbox = _lesson_counts_for_module(obj)
        return _format_lesson_counts(theory, radio, checkbox)

    @admin.display(description=_("Статистика"))
    def lessons_count_display(self, obj):
        theory_count = obj.lessons_theories.count()
        radio_count = obj.lessons_radio_questions.count()
        checkbox_count = obj.lessons_checkbox_questions.count()
        total = theory_count + radio_count + checkbox_count

        stats_html = f"""
            <div style="
                padding: 0.75rem;
                background: var(--primary-bg);
                border-radius: 0.375rem;
                border: 1px solid var(--border-color);
                font-size: 0.875rem;
            ">
                <div style="margin-bottom: 0.25rem;">
                    <span style="
                        display: inline-block;
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background: #0d6efd;
                        margin-right: 0.5rem;
                    "></span>
                    <strong>{_('Теория')}:</strong> {theory_count}
                </div>
                <div style="margin-bottom: 0.25rem;">
                    <span style="
                        display: inline-block;
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background: #198754;
                        margin-right: 0.5rem;
                    "></span>
                    <strong>{_('Радио')}:</strong> {radio_count}
                </div>
                <div>
                    <span style="
                        display: inline-block;
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background: #ffc107;
                        margin-right: 0.5rem;
                    "></span>
                    <strong>{_('Чекбоксы')}:</strong> {checkbox_count}
                </div>
                <hr style="margin: 0.5rem 0;
                border-color: var(--border-color);">
                <div>
                    <strong>{_('Всего')}:</strong> {total}
                </div>
            </div>
            """
        return format_html(stats_html)

    @display(description=_("Действия"), label=True)
    def actions_column(self, obj):
        return _open_link(
            reverse("admin:content_module_change", args=[obj.id])
        )

    @action(description=_("Активировать модули ✅"), permissions=["change"])
    def activate_modules(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f"{updated} модулей активировано ✅"),
            messages.SUCCESS,
        )

    @action(description=_("Деактивировать модули ❌"), permissions=["change"])
    def deactivate_modules(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f"{updated} модулей деактивировано ❌"),
            messages.WARNING,
        )

    actions = ["activate_modules", "deactivate_modules"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("course").prefetch_related(
            "lessons_theories",
            "lessons_radio_questions",
            "lessons_checkbox_questions",
        )


@admin.register(LessonTheory)
class LessonTheoryAdmin(ModelAdmin):
    """Админка для теоретических уроков"""

    list_display = (
        "title",
        "module_link",
        "course_link",
        "content_preview",
        "is_active",
        "actions_column",
    )
    list_filter = (
        "is_active",
        "module__course",
        "module",
    )
    search_fields = (
        "title",
        "content",
        "module__title",
        "module__course__title",
    )
    list_per_page = 20
    ordering = ("module", "order_index")
    readonly_fields = ("created_info",)
    icon = "article"

    fieldsets = (
        (
            _("Основная информация"),
            {
                "fields": (
                    "module",
                    "title",
                    "content",
                    "is_active",
                ),
            },
        ),
        (
            _("Дополнительная информация"),
            {
                "fields": ("created_info",),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Содержание"))
    def content_preview(self, obj):
        if not obj.content:
            return "—"
        preview = (
            obj.content[:100] + "..."
            if len(obj.content) > 100
            else obj.content
        )
        return format_html('<span title="{}">{}</span>', obj.content, preview)

    @admin.display(description=_("Модуль"), ordering="module__title")
    def module_link(self, obj):
        url = reverse("admin:content_module_change", args=[obj.module.id])
        return format_html('<a href="{}">{}</a>', url, obj.module.title)

    @admin.display(description=_("Курс"), ordering="module__course__title")
    def course_link(self, obj):
        url = reverse(
            "admin:content_course_change", args=[obj.module.course.id]
        )
        return format_html('<a href="{}">{}</a>', url, obj.module.course.title)

    @admin.display(description=_("Информация"))
    def created_info(self, obj):
        info_html = f"""
        <div style="
            padding: 0.75rem;
            background: var(--primary-bg);
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 0.875rem;
        ">
            <div style="margin-bottom: 0.5rem;">
                <strong style="color: var(--primary-text);">
                {_('Курс')}:
                </strong>
                <span style="color:
                var(--secondary-text); margin-left: 0.25rem;">
                    {obj.module.course.title}
                </span>
            </div>
            <div>
                <strong style="color: var(--primary-text);">
                {_('Модуль')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {obj.module.title}
                </span>
            </div>
        </div>
        """
        return format_html(info_html)

    @display(description=_("Действия"), label=True)
    def actions_column(self, obj):
        return _open_link(
            reverse("admin:content_lessontheory_change", args=[obj.id])
        )

    @action(description=_("Активировать уроки ✅"), permissions=["change"])
    def activate_lessons(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f"{updated} уроков активировано ✅"),
            messages.SUCCESS,
        )

    @action(description=_("Деактивировать уроки ❌"), permissions=["change"])
    def deactivate_lessons(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f"{updated} уроков деактивировано ❌"),
            messages.WARNING,
        )

    actions = ["activate_lessons", "deactivate_lessons"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("module", "module__course")


class RadioAnswerOptionInline(TabularInline):
    model = RadioAnswerOption
    extra = 2
    max_num = 10
    ordering = ("order_index",)
    ordering_field = "order_index"
    hide_ordering_field = True
    fields = ("text", "is_correct")

    def get_extra(self, request, obj=None, **kwargs):
        if not obj:
            return 4
        return self.extra


class CheckBoxAnswerOptionInline(TabularInline):
    model = CheckBoxAnswerOption
    extra = 2
    max_num = 10
    ordering = ("order_index",)
    ordering_field = "order_index"
    hide_ordering_field = True
    fields = ("text", "is_correct")

    def get_extra(self, request, obj=None, **kwargs):
        if not obj:
            return 4
        return self.extra


@admin.register(LessonRadioQuestion)
class LessonRadioQuestionAdmin(ModelAdmin):
    list_display = (
        "title",
        "module_link",
        "course_link",
        "answers_count",
        "correct_answer_preview",
        "points",
        "is_active",
        "actions_column",
    )
    list_filter = (
        "is_active",
        "module__course",
        "module",
    )
    search_fields = (
        "title",
        "question_text",
        "explanation",
        "module__title",
        "module__course__title",
    )
    list_per_page = 20
    ordering = ("module", "order_index")
    readonly_fields = ("question_stats", "created_info")
    icon = "radio_button_checked"

    fieldsets = (
        (
            _("Основная информация"),
            {
                "fields": (
                    "module",
                    "title",
                    "question_text",
                    "explanation",
                    "points",
                    "is_active",
                ),
            },
        ),
        (
            _("Статистика"),
            {
                "fields": ("question_stats",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Дополнительная информация"),
            {
                "fields": ("created_info",),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [RadioAnswerOptionInline]

    @admin.display(description=_("Модуль"), ordering="module__title")
    def module_link(self, obj):
        url = reverse("admin:content_module_change", args=[obj.module.id])
        return format_html('<a href="{}">{}</a>', url, obj.module.title)

    @admin.display(description=_("Курс"), ordering="module__course__title")
    def course_link(self, obj):
        url = reverse(
            "admin:content_course_change", args=[obj.module.course.id]
        )
        return format_html('<a href="{}">{}</a>', url, obj.module.course.title)

    @admin.display(description=_("Ответы"))
    def answers_count(self, obj):
        count = obj.answers.count()
        if count == 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: 500;">⚠️ {}</span>',
                _("Нет ответов"),
            )

        correct = obj.answers.filter(is_correct=True).count()
        if correct == 0:
            return format_html(
                '<span style="color: #ffc107;">{} {} (⚠️ {})</span>',
                count,
                _("ответов"),
                _("нет правильных"),
            )
        elif correct > 1:
            return format_html(
                '<span style="color: #ffc107;">{} {} (⚠️ {} {})</span>',
                count,
                _("ответов"),
                correct,
                _("правильных"),
            )

        return format_html(
            '<span style="color: #198754;">{} {}</span>', count, _("ответов")
        )

    @admin.display(description=_("Правильный ответ"))
    def correct_answer_preview(self, obj):
        correct = obj.get_correct_answer()
        if not correct:
            return format_html(
                '<span style="color: #dc3545;">❌ {}</span>',
                _("Нет правильного ответа"),
            )

        preview = (
            correct.text[:50] + "..."
            if len(correct.text) > 50
            else correct.text
        )
        return format_html(
            '<span style="color: #198754;">✅ {}</span>', preview
        )

    @admin.display(description=_("Статистика"))
    def question_stats(self, obj):
        total_answers = obj.answers.count()
        correct_answers = obj.answers.filter(is_correct=True).count()

        stats_html = f"""
        <div style="
            padding: 0.75rem;
            background: var(--primary-bg);
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 0.875rem;
        ">
            <div style="margin-bottom: 0.5rem; display: flex;
            align-items: center;">
                <span style="
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #0d6efd;
                    margin-right: 0.5rem;
                "></span>
                <strong style="color: var(--primary-text);">
                {_('Всего ответов')}:</strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {total_answers}
                </span>
            </div>
            <div style="display: flex; align-items: center;">
                <span style="
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #198754;
                    margin-right: 0.5rem;
                "></span>
                <strong style="color: var(--primary-text);">
                {_('Правильных ответов')}:</strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {correct_answers}
                </span>
            </div>
        </div>
        """
        return format_html(stats_html)

    @admin.display(description=_("Информация"))
    def created_info(self, obj):
        info_html = f"""
        <div style="
            padding: 0.75rem;
            background: var(--primary-bg);
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 0.875rem;
        ">
            <div style="margin-bottom: 0.5rem;">
                <strong style="color: var(--primary-text);">
                {_('Курс')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {obj.module.course.title}
                </span>
            </div>
            <div>
                <strong style="color: var(--primary-text);">
                {_('Модуль')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {obj.module.title}
                </span>
            </div>
        </div>
        """
        return format_html(info_html)

    @display(description=_("Действия"), label=True)
    def actions_column(self, obj):
        return _open_link(
            reverse("admin:content_lessonradioquestion_change", args=[obj.id])
        )

    @action(description=_("Активировать вопросы ✅"), permissions=["change"])
    def activate_questions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f"{updated} радио-вопросов активировано ✅"),
            messages.SUCCESS,
        )

    @action(description=_("Деактивировать вопросы ❌"), permissions=["change"])
    def deactivate_questions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f"{updated} радио-вопросов деактивировано ❌"),
            messages.WARNING,
        )

    @action(description=_("Установить 1 балл"), permissions=["change"])
    def set_points_one(self, request, queryset):
        updated = queryset.update(points=1)
        self.message_user(
            request,
            _(f"{updated} вопросов обновлено до 1 балла"),
            messages.SUCCESS,
        )

    @action(description=_("Установить 5 баллов"), permissions=["change"])
    def set_points_five(self, request, queryset):
        updated = queryset.update(points=5)
        self.message_user(
            request,
            _(f"{updated} вопросов обновлено до 5 баллов"),
            messages.SUCCESS,
        )

    actions = [
        "activate_questions",
        "deactivate_questions",
        "set_points_one",
        "set_points_five",
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "module", "module__course"
        ).prefetch_related("answers")


@admin.register(LessonCheckBoxQuestion)
class LessonCheckBoxQuestionAdmin(ModelAdmin):
    """Админка для чекбокс-вопросов"""

    list_display = (
        "title",
        "module_link",
        "course_link",
        "answers_count",
        "correct_answers_count",
        "points",
        "is_active",
        "actions_column",
    )
    list_filter = (
        "is_active",
        "module__course",
        "module",
    )
    search_fields = (
        "title",
        "question_text",
        "explanation",
        "module__title",
        "module__course__title",
    )
    list_per_page = 20
    ordering = ("module", "order_index")
    readonly_fields = ("question_stats", "created_info")
    icon = "check_box"

    fieldsets = (
        (
            _("Основная информация"),
            {
                "fields": (
                    "module",
                    "title",
                    "question_text",
                    "explanation",
                    "points",
                    "is_active",
                ),
            },
        ),
        (
            _("Статистика"),
            {
                "fields": ("question_stats",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Дополнительная информация"),
            {
                "fields": ("created_info",),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [CheckBoxAnswerOptionInline]

    @admin.display(description=_("Модуль"), ordering="module__title")
    def module_link(self, obj):
        url = reverse("admin:content_module_change", args=[obj.module.id])
        return format_html('<a href="{}">{}</a>', url, obj.module.title)

    @admin.display(description=_("Курс"), ordering="module__course__title")
    def course_link(self, obj):
        url = reverse(
            "admin:content_course_change", args=[obj.module.course.id]
        )
        return format_html('<a href="{}">{}</a>', url, obj.module.course.title)

    @admin.display(description=_("Ответы"))
    def answers_count(self, obj):
        count = obj.answers.count()
        if count == 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: 500;">⚠️ {}</span>',
                _("Нет ответов"),
            )

        return format_html(
            '<span style="color: #0d6efd;">{} {}</span>', count, _("ответов")
        )

    @admin.display(description=_("Правильные"))
    def correct_answers_count(self, obj):
        correct = obj.answers.filter(is_correct=True).count()

        if correct == 0:
            return format_html('<span style="color: #dc3545;">❌ 0</span>')
        elif correct == 1:
            return format_html('<span style="color: #ffc107;">⚠️ 1</span>')

        return format_html(
            '<span style="color: #198754;">✅ {}</span>', correct
        )

    @admin.display(description=_("Статистика"))
    def question_stats(self, obj):
        total_answers = obj.answers.count()
        correct_answers = obj.answers.filter(is_correct=True).count()
        incorrect_answers = total_answers - correct_answers

        stats_html = f"""
        <div style="
            padding: 0.75rem;
            background: var(--primary-bg);
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 0.875rem;
        ">
            <div style="margin-bottom: 0.5rem; display: flex;
            align-items: center;">
                <span style="
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #0d6efd;
                    margin-right: 0.5rem;
                "></span>
                <strong style="color: var(--primary-text);">
                {_('Всего ответов')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {total_answers}
                </span>
            </div>
            <div style="margin-bottom: 0.5rem; display: flex;
            align-items: center;">
                <span style="
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #198754;
                    margin-right: 0.5rem;
                "></span>
                <strong style="color: var(--primary-text);">{_('Правильные')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {correct_answers}
                </span>
            </div>
            <div style="display: flex; align-items: center;">
                <span style="
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #dc3545;
                    margin-right: 0.5rem;
                "></span>
                <strong style="color: var(--primary-text);">
                {_('Неправильные')}:</strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {incorrect_answers}
                </span>
            </div>
        </div>
        """
        return format_html(stats_html)

    @admin.display(description=_("Информация"))
    def created_info(self, obj):
        info_html = f"""
        <div style="
            padding: 0.75rem;
            background: var(--primary-bg);
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 0.875rem;
        ">
            <div style="margin-bottom: 0.5rem;">
                <strong style="color: var(--primary-text);">
                {_('Курс')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {obj.module.course.title}
                </span>
            </div>
            <div>
                <strong style="color: var(--primary-text);">
                {_('Модуль')}:
                </strong>
                <span style="color: var(--secondary-text);
                margin-left: 0.25rem;">
                    {obj.module.title}
                </span>
            </div>
        </div>
        """
        return format_html(info_html)

    @display(description=_("Действия"), label=True)
    def actions_column(self, obj):
        return _open_link(
            reverse(
                "admin:content_lessoncheckboxquestion_change", args=[obj.id]
            )
        )

    @action(description=_("Активировать вопросы ✅"), permissions=["change"])
    def activate_questions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f"{updated} чекбокс-вопросов активировано ✅"),
            messages.SUCCESS,
        )

    @action(description=_("Деактивировать вопросы ❌"), permissions=["change"])
    def deactivate_questions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f"{updated} чекбокс-вопросов деактивировано ❌"),
            messages.WARNING,
        )

    actions = ["activate_questions", "deactivate_questions"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "module", "module__course"
        ).prefetch_related("answers")


@admin.register(CodingChallenge)
class CodingChallengeAdmin(ModelAdmin):
    """Админка для задач по программированию"""

    list_display = (
        "title",
        "public_id",
        "difficulty_badge",
        "points",
        "course_link",
        "module_link",
        "solved_count",
        "is_active",
    )
    list_filter = (
        "difficulty",
        "is_active",
        "course",
        "module",
    )
    search_fields = ("title", "description", "instructions")
    list_per_page = 20
    ordering = ("order_index", "difficulty", "title")
    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
        "stats_display",
    )
    icon = "code"

    fieldsets = (
        (
            _("Основная информация"),
            {
                "fields": (
                    "public_id",
                    "title",
                    "description",
                    "instructions",
                    "difficulty",
                    "points",
                ),
            },
        ),
        (
            _("Код и ограничения"),
            {
                "fields": (
                    "initial_code",
                    "solution_template",
                    "time_limit_ms",
                    "memory_limit_mb",
                ),
            },
        ),
        (
            _("Привязка к курсу"),
            {
                "fields": (
                    "course",
                    "module",
                    "is_active",
                ),
            },
        ),
        (
            _("Статистика"),
            {
                "fields": ("stats_display",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Даты"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @display(description=_("Сложность"))
    def difficulty_badge(self, obj):
        colors = {
            "beginner": "#6c757d",  # серый
            "easy": "#198754",  # зеленый
            "medium": "#ffc107",  # желтый
            "hard": "#fd7e14",  # оранжевый
            "expert": "#dc3545",  # красный
        }
        names = {
            "beginner": _("Начинающий"),
            "easy": _("Легкий"),
            "medium": _("Средний"),
            "hard": _("Сложный"),
            "expert": _("Эксперт"),
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 0.75rem;">{}</span>',
            colors.get(obj.difficulty, "#6c757d"),
            names.get(obj.difficulty, obj.difficulty),
        )

    @display(description=_("Курс"), ordering="course__title")
    def course_link(self, obj):
        if not obj.course:
            return "—"
        url = reverse("admin:content_course_change", args=[obj.course.id])
        return format_html('<a href="{}">{}</a>', url, obj.course.title)

    @display(description=_("Модуль"), ordering="module__title")
    def module_link(self, obj):
        if not obj.module:
            return "—"
        url = reverse("admin:content_module_change", args=[obj.module.id])
        return format_html('<a href="{}">{}</a>', url, obj.module.title)

    @display(description=_("Решено"))
    def solved_count(self, obj):
        count = obj.submissions.filter(status="completed").count()
        if count == 0:
            return "—"
        url = (
            reverse("admin:progress_codesubmission_changelist")
            + f"?challenge__id__exact={obj.id}"
        )
        return format_html('<a href="{}">{}</a>', url, count)

    @display(description=_("Статистика"))
    def stats_display(self, obj):
        total = obj.submissions.count()
        completed = obj.submissions.filter(status="completed").count()
        success_rate = obj.success_rate

        stats_html = f"""
        <div style="
            padding: 0.75rem;
            background: var(--primary-bg);
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 0.875rem;
        ">
            <div style="margin-bottom: 0.5rem;">
                <strong>{_('Всего отправок')}:</strong> {total}
            </div>
            <div style="margin-bottom: 0.5rem;">
                <strong>{_('Успешных отправок')}:</strong> {completed}
            </div>
            <div>
                <strong>{_('Процент успеха')}:</strong>
                <span style="color: {'#198754'
                if success_rate >= 50 else '#ffc107'
                if success_rate > 0 else '#dc3545'}">
                    {success_rate}%
                </span>
            </div>
        </div>
        """
        return format_html(stats_html)

    @action(description=_("Активировать"), permissions=["change"])
    def activate_challenges(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request, _(f"{updated} задач активировано ✅"), messages.SUCCESS
        )

    @action(description=_("Деактивировать"), permissions=["change"])
    def deactivate_challenges(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request, _(f"{updated} задач деактивировано ❌"), messages.WARNING
        )

    actions = ["activate_challenges", "deactivate_challenges"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("submissions")


class TestCaseInline(TabularInline):
    """Инлайн для тестовых случаев"""

    model = TestCase
    extra = 1
    ordering = ("order_index",)
    ordering_field = "order_index"
    hide_ordering_field = True
    fields = ("input_data", "expected_output", "is_hidden")


# Добавляем inlines в CodingChallengeAdmin
CodingChallengeAdmin.inlines = [TestCaseInline]


@admin.register(TestCase)
class TestCaseAdmin(ModelAdmin):
    """Админка для тестовых случаев"""

    list_display = (
        "challenge_link",
        "input_preview",
        "output_preview",
        "is_hidden",
    )
    list_filter = ("is_hidden", "challenge")
    search_fields = ("challenge__title", "input_data", "expected_output")
    list_per_page = 20
    ordering = ("challenge", "order_index")
    icon = "fact_check"

    @display(description=_("Задача"), ordering="challenge__title")
    def challenge_link(self, obj):
        url = reverse(
            "admin:content_codingchallenge_change", args=[obj.challenge.id]
        )
        return format_html('<a href="{}">{}</a>', url, obj.challenge.title)

    @display(description=_("Входные данные"))
    def input_preview(self, obj):
        preview = (
            obj.input_data[:50] + "..."
            if len(obj.input_data) > 50
            else obj.input_data
        )
        return format_html(
            '<code title="{}">{}</code>', obj.input_data, preview
        )

    @display(description=_("Ожидаемый вывод"))
    def output_preview(self, obj):
        preview = (
            obj.expected_output[:50] + "..."
            if len(obj.expected_output) > 50
            else obj.expected_output
        )
        return format_html(
            '<code title="{}">{}</code>', obj.expected_output, preview
        )
