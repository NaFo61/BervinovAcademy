from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import action, display

from progress.models import (
    CodeSubmission,
    LessonUserComment,
    UserAnswerCheckBox,
    UserAnswerRadio,
)


@admin.register(UserAnswerRadio)
class UserAnswerRadioAdmin(ModelAdmin):
    """Админка для ответов на radio-вопросы"""

    list_display = (
        "user_info",
        "question_info",
        "selected_answer_preview",
        "result_badge",
        "points_display",
        "created_at",
        "actions_column",
    )

    list_filter = (
        "is_correct",
        "question__module__course",
        "question__module",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__phone",
        "user__first_name",
        "user__last_name",
        "question__title",
        "question__question_text",
        "selected_answer__text",
    )

    list_per_page = 20
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "answer_details",
        "is_correct",  # Только для чтения
        "points_earned",  # Только для чтения
        "selected_answer_display",  # Кастомное поле для отображения ответа
    )
    icon = "radio_button_checked"

    fieldsets = (
        (
            _("Пользователь и вопрос"),
            {
                "fields": (
                    "user",
                    "question",
                ),
            },
        ),
        (
            _("Ответ"),
            {
                "fields": (
                    "selected_answer_display",
                    # Заменяем selected_answer на отображаемое поле
                    "is_correct",
                    "points_earned",
                ),
            },
        ),
        (
            _("Детали ответа"),
            {
                "fields": ("answer_details",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Временные метки"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        """Настройка формы для ограничения выбора ответов"""
        form = super().get_form(request, obj, **kwargs)

        if obj and obj.question:  # Если есть объект и вопрос
            # Ограничиваем поле selected_answer только ответами,
            # принадлежащими текущему вопросу
            form.base_fields["selected_answer"].queryset = (
                obj.question.answers.all()
            )
            # Делаем поле обязательным и видимым
            form.base_fields["selected_answer"].required = True

        return form

    @display(description=_("Выбранный ответ"))
    def selected_answer_display(self, obj):
        """Отображение выбранного ответа (только для чтения)"""
        if not obj or not obj.selected_answer:
            return "—"

        # Показываем ответ с индикатором правильности
        is_correct = obj.selected_answer.is_correct
        icon = "✅" if is_correct else "❌"

        return format_html(
            '<div style="padding: 8px; background: {}; border-radius: 4px;">'
            "{} {}<br>"
            '<small style="color: #666;">{}</small>'
            "</div>",
            "#d4edda" if is_correct else "#f8d7da",
            icon,
            obj.selected_answer.text,
            _("Правильный ответ") if is_correct else _("Неправильный ответ"),
        )

    selected_answer_display.short_description = _("Выбранный ответ")

    # Скрываем оригинальное поле selected_answer из формы
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # Можно также полностью исключить поле из формы
        return fieldsets

    # Остальные методы остаются без изменений...
    @display(description=_("Пользователь"), ordering="user__email")
    def user_info(self, obj):
        """Информация о пользователе"""
        url = reverse("admin:users_user_change", args=[obj.user.id])
        name = obj.user.get_full_name() or str(obj.user)
        return format_html(
            '<a href="{}" style="font-weight: 500;">{}</a><br>'
            '<span style="font-size: 0.85em; color: #666;">{}</span>',
            url,
            name,
            obj.user.email or obj.user.phone or "—",
        )

    @display(description=_("Вопрос"), ordering="question__title")
    def question_info(self, obj):
        """Информация о вопросе"""
        url = reverse(
            "admin:content_lessonradioquestion_change", args=[obj.question.id]
        )
        return format_html(
            '<a href="{}" style="font-weight: 500;">{}</a><br>'
            '<span style="font-size: 0.85em; color: #666;">{} → {}</span>',
            url,
            obj.question.title,
            obj.question.module.course.title,
            obj.question.module.title,
        )

    @display(description=_("Выбранный ответ"))
    def selected_answer_preview(self, obj):
        """Превью выбранного ответа (для list_display)"""
        preview = obj.selected_answer.text
        if len(preview) > 60:
            preview = preview[:60] + "..."

        icon = "✅" if obj.selected_answer.is_correct else "❌"

        return format_html(
            '<span title="{}">{} {}</span>',
            obj.selected_answer.text,
            icon,
            preview,
        )

    @display(description=_("Результат"))
    def result_badge(self, obj):
        """Бейдж с результатом"""
        if obj.is_correct:
            return format_html(
                '<span style="'
                "display: inline-block; "
                "padding: 4px 8px; "
                "background: #d4edda; "
                "color: #155724; "
                "border-radius: 4px; "
                "font-weight: 500; "
                "font-size: 0.85em;"
                '">✅ {}</span>',
                _("Правильно"),
            )
        return format_html(
            '<span style="'
            "display: inline-block; "
            "padding: 4px 8px; "
            "background: #f8d7da; "
            "color: #721c24; "
            "border-radius: 4px; "
            "font-weight: 500; "
            "font-size: 0.85em;"
            '">❌ {}</span>',
            _("Неправильно"),
        )

    @display(description=_("Баллы"))
    def points_display(self, obj):
        """Отображение баллов"""
        if obj.points_earned > 0:
            return format_html(
                '<span style="color: #198754; font-weight: 600;">+{}</span>',
                obj.points_earned,
            )
        return format_html('<span style="color: #dc3545;">0</span>')

    @display(description=_("Действия"), label=True)
    def actions_column(self, obj):
        """Колонка с действиями"""
        return format_html(
            """
            <div style="display: flex; gap: 5px;">
                <a href="{view}" style="color: #0d6efd;"
                title="{view_title}">👁️</a>
                <a href="{edit}" style="color: #198754;"
                title="{edit_title}">✏️</a>
                <a href="{user}" style="color: #6f42c1;"
                title="{user_title}">👤</a>
            </div>
            """,
            view=reverse(
                "admin:progress_useranswerradio_change", args=[obj.id]
            ),
            edit=reverse(
                "admin:progress_useranswerradio_change", args=[obj.id]
            ),
            user=reverse("admin:users_user_change", args=[obj.user.id]),
            view_title=_("Просмотр"),
            edit_title=_("Редактировать"),
            user_title=_("Профиль пользователя"),
        )

    @display(description=_("Детали ответа"))
    def answer_details(self, obj):
        """Детальная информация об ответе"""
        # Все попытки по этому вопросу (несколько POST в API на один вопрос).
        all_answers = UserAnswerRadio.objects.filter(
            user=obj.user, question=obj.question
        ).order_by("-created_at")

        history_html = ""
        if all_answers.count() > 1:
            history_items = []
            for i, answer in enumerate(all_answers):
                if i < 5:  # Показываем только последние 5
                    status = "✅" if answer.is_correct else "❌"
                    history_items.append(
                        f'<div style="margin-bottom: '
                        f'0.25rem; font-size: 0.9em;">'
                        f"{status} "
                        f'{answer.created_at.strftime("%d.%m.%Y %H:%M")} '
                        f"- {answer.selected_answer.text[:30]}..."
                        f"</div>"
                    )

            if history_items:
                extra_count = all_answers.count() - 5
                extra_html = (
                    f'<div style="color: #666; font-size: 0.85em;">... +'
                    f'{extra_count} {_("еще")}</div>'
                    if extra_count > 0
                    else ""
                )

                history_html = f"""
                <div style="margin-top: 1rem;">
                    <strong style="color: var(--primary-text);">
                    {_('История попыток по вопросу')}:
                    </strong>
                    <div style="margin-top: 0.5rem; padding-left: 0.5rem;
                    border-left: 2px solid #dee2e6;">
                        {''.join(history_items)}
                        {extra_html}
                    </div>
                </div>
                """

        correct_answer = obj.question.get_correct_answer()
        correct_answer_text = correct_answer.text if correct_answer else "—"

        details_html = f"""
        <div style="
            padding: 1rem;
            background: var(--primary-bg);
            border-radius: 0.5rem;
            border: 1px solid var(--border-color);
            font-size: 0.95rem;
        ">
            <div style="margin-bottom: 1rem;">
                <div style="margin-bottom: 0.5rem;">
                    <strong style="color: var(--primary-text);">
                    {_('Вопрос')}:
                    </strong>
                </div>
                <div style="padding: 0.75rem; background: rgba(0,0,0,0.02);
                border-radius: 0.375rem; border: 1px
                solid var(--border-color);">
                    {obj.question.question_text}
                </div>
            </div>

            <div style="margin-bottom: 1rem;">
                <div style="margin-bottom: 0.5rem;">
                    <strong style="color: var(--primary-text);">
                    {_('Правильный ответ')}:
                    </strong>
                </div>
                <div style="padding: 0.75rem; background: #d4edda;
                border-radius: 0.375rem; color: #155724;">
                    ✅ {correct_answer_text}
                </div>
            </div>

            {history_html}
        </div>
        """
        return format_html(details_html)

    @action(
        description=_("Отметить как правильные ✅"), permissions=["change"]
    )
    def mark_as_correct(self, request, queryset):
        """Отметить выбранные ответы как правильные"""
        updated = 0
        for obj in queryset:
            if not obj.is_correct:
                obj.is_correct = True
                obj.points_earned = obj.question.points
                obj.save()
                updated += 1
        self.message_user(
            request,
            _(f"{updated} ответов отмечено как правильные ✅"),
            messages.SUCCESS,
        )

    @action(
        description=_("Отметить как неправильные ❌"), permissions=["change"]
    )
    def mark_as_incorrect(self, request, queryset):
        """Отметить выбранные ответы как неправильные"""
        updated = queryset.update(is_correct=False, points_earned=0)
        self.message_user(
            request,
            _(f"{updated} ответов отмечено как неправильные ❌"),
            messages.WARNING,
        )

    actions = ["mark_as_correct", "mark_as_incorrect"]

    def get_queryset(self, request):
        """Оптимизация запросов"""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "user",
            "question",
            "question__module",
            "question__module__course",
            "selected_answer",
        )

    def has_change_permission(self, request, obj=None):
        """Разрешаем изменение, но с нашими ограничениями"""
        return True


@admin.register(UserAnswerCheckBox)
class UserAnswerCheckBoxAdmin(ModelAdmin):
    """Админка для ответов на checkbox-вопросы"""

    list_display = (
        "user_info",
        "question_info",
        "selected_answers_preview",
        "result_badge",
        "points_display",
        "created_at",
        "actions_column",
    )

    list_filter = (
        "is_correct",
        "question__module__course",
        "question__module",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__phone",
        "user__first_name",
        "user__last_name",
        "question__title",
        "question__question_text",
    )

    list_per_page = 20
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "answer_details",
        "selected_answers_display",  # Кастомное поле для отображения
        "is_correct",  # Только для чтения
        "points_earned",  # Только для чтения
    )
    icon = "check_box"

    fieldsets = (
        (
            _("Пользователь и вопрос"),
            {
                "fields": (
                    "user",
                    "question",
                ),
            },
        ),
        (
            _("Ответ"),
            {
                "fields": (
                    "selected_answers_display",  # Заменяем selected_answers
                    "is_correct",
                    "points_earned",
                ),
            },
        ),
        (
            _("Детали ответа"),
            {
                "fields": ("answer_details",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Временные метки"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        """Настройка формы для ограничения выбора ответов"""
        form = super().get_form(request, obj, **kwargs)

        if obj and obj.question:  # Если есть объект и вопрос
            # Ограничиваем поле selected_answers только ответами,
            # принадлежащими текущему вопросу
            if "selected_answers" in form.base_fields:
                form.base_fields["selected_answers"].queryset = (
                    obj.question.answers.all()
                )

        return form

    @display(description=_("Выбранные ответы"))
    def selected_answers_display(self, obj):
        """Отображение выбранных ответов (только для чтения)"""
        if not obj or not obj.pk:
            return "—"

        answers = obj.selected_answers.all()
        if not answers:
            return "—"

        # Получаем все правильные ответы для сравнения
        correct_answers = set(obj.question.answers.filter(is_correct=True))

        items = []
        for answer in answers:
            is_correct = answer.is_correct
            # Проверяем, должен ли этот ответ быть выбран
            answer in correct_answers
            icon = "✅" if is_correct else "❌"

            items.append(
                f'<div style="margin-bottom: 0.5rem; padding: 4px 8px; '
                f'background: {"#d4edda" if is_correct else "#f8d7da"}; '
                f'border-radius: 4px;">'
                f"{icon} {answer.text}"
                f'{" (правильный)" if is_correct else " (неправильный)"}'
                f"</div>"
            )

        return format_html("".join(items))

    selected_answers_display.short_description = _("Выбранные ответы")

    # Остальные методы остаются без изменений...
    @display(description=_("Пользователь"), ordering="user__email")
    def user_info(self, obj):
        """Информация о пользователе"""
        url = reverse("admin:users_user_change", args=[obj.user.id])
        name = obj.user.get_full_name() or str(obj.user)
        return format_html(
            '<a href="{}" style="font-weight: 500;">{}</a><br>'
            '<span style="font-size: 0.85em; color: #666;">{}</span>',
            url,
            name,
            obj.user.email or obj.user.phone or "—",
        )

    @display(description=_("Вопрос"), ordering="question__title")
    def question_info(self, obj):
        """Информация о вопросе"""
        url = reverse(
            "admin:content_lessoncheckboxquestion_change",
            args=[obj.question.id],
        )
        return format_html(
            '<a href="{}" style="font-weight: 500;">{}</a><br>'
            '<span style="font-size: 0.85em; color: #666;">{} → {}</span>',
            url,
            obj.question.title,
            obj.question.module.course.title,
            obj.question.module.title,
        )

    @display(description=_("Выбранные ответы"))
    def selected_answers_preview(self, obj):
        """Превью выбранных ответов (для list_display)"""
        answers = obj.selected_answers.all()
        if not answers:
            return "—"

        preview_parts = []
        for answer in answers[:2]:
            icon = "✅" if answer.is_correct else "❌"
            text = (
                answer.text[:30] + "..."
                if len(answer.text) > 30
                else answer.text
            )
            preview_parts.append(f"{icon} {text}")

        preview = ", ".join(preview_parts)
        if answers.count() > 2:
            preview += f" (+{answers.count() - 2})"

        return format_html(
            '<span title="{}">{}</span>',
            "\n".join(
                [f"{'✅' if a.is_correct else '❌'} {a.text}" for a in answers]
            ),
            preview,
        )

    @display(description=_("Результат"))
    def result_badge(self, obj):
        """Бейдж с результатом"""
        if obj.is_correct:
            return format_html(
                '<span style="'
                "display: inline-block; "
                "padding: 4px 8px; "
                "background: #d4edda; "
                "color: #155724; "
                "border-radius: 4px; "
                "font-weight: 500; "
                "font-size: 0.85em;"
                '">✅ {}</span>',
                _("Правильно"),
            )
        return format_html(
            '<span style="'
            "display: inline-block; "
            "padding: 4px 8px; "
            "background: #f8d7da; "
            "color: #721c24; "
            "border-radius: 4px; "
            "font-weight: 500; "
            "font-size: 0.85em;"
            '">❌ {}</span>',
            _("Неправильно"),
        )

    @display(description=_("Баллы"))
    def points_display(self, obj):
        """Отображение баллов"""
        if obj.points_earned > 0:
            return format_html(
                '<span style="color: #198754; font-weight: 600;">+{}</span>',
                obj.points_earned,
            )
        return format_html('<span style="color: #dc3545;">0</span>')

    @display(description=_("Действия"), label=True)
    def actions_column(self, obj):
        """Колонка с действиями"""
        return format_html(
            """
            <div style="display: flex; gap: 5px;">
                <a href="{view}" style="color: #0d6efd;"
                title="{view_title}">👁️</a>
                <a href="{edit}" style="color: #198754;"
                title="{edit_title}">✏️</a>
                <a href="{user}" style="color: #6f42c1;"
                title="{user_title}">👤</a>
            </div>
            """,
            view=reverse(
                "admin:progress_useranswercheckbox_change", args=[obj.id]
            ),
            edit=reverse(
                "admin:progress_useranswercheckbox_change", args=[obj.id]
            ),
            user=reverse("admin:users_user_change", args=[obj.user.id]),
            view_title=_("Просмотр"),
            edit_title=_("Редактировать"),
            user_title=_("Профиль пользователя"),
        )

    @display(description=_("Детали ответа"))
    def answer_details(self, obj):
        """Детальная информация об ответе на checkbox-вопрос"""
        # Правильные ответы
        correct_answers = obj.question.answers.filter(is_correct=True)
        correct_list = "".join(
            [
                f'<div style="margin-bottom: 0.25rem;">✅ {a.text}</div>'
                for a in correct_answers
            ]
        )

        # Выбранные ответы
        selected = obj.selected_answers.all()
        selected_list = "".join(
            [
                f'<div style="margin-bottom: 0.25rem; padding: 2px 4px; '
                f'background: {"#d4edda" if a.is_correct else "#f8d7da"}; '
                f'border-radius: 4px;">'
                f'{"✅" if a.is_correct else "❌"} {a.text}'
                f"</div>"
                for a in selected
            ]
        )

        # Невыбранные правильные ответы
        not_selected_correct = correct_answers.exclude(
            id__in=[a.id for a in selected]
        )
        missing_list = ""
        if not_selected_correct.exists():
            missing_list = "".join(
                [
                    f'<div style="margin-bottom: 0.25rem; color: #dc3545;">⚠️ '
                    f'{a.text} ({_("не выбран")})</div>'
                    for a in not_selected_correct
                ]
            )

        # Выбранные неправильные ответы
        incorrect_selected = selected.exclude(is_correct=True)
        extra_list = ""
        if incorrect_selected.exists():
            extra_list = "".join(
                [
                    f'<div style="margin-bottom: 0.25rem; color: #dc3545;">❌ '
                    f'{a.text} ({_("лишний")})</div>'
                    for a in incorrect_selected
                ]
            )

        details_html = f"""
        <div style="
            padding: 1rem;
            background: var(--primary-bg);
            border-radius: 0.5rem;
            border: 1px solid var(--border-color);
            font-size: 0.95rem;
        ">
            <div style="margin-bottom: 1rem;">
                <div style="margin-bottom: 0.5rem;">
                    <strong style="color: var(--primary-text);">
                    {_('Вопрос')}:
                    </strong>
                </div>
                <div style="padding: 0.75rem; background: rgba(0,0,0,0.02);
                border-radius: 0.375rem; border: 1px solid
                var(--border-color);">
                    {obj.question.question_text}
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr;
            gap: 1rem; margin-bottom: 1rem;">
                <div>
                    <div style="margin-bottom: 0.5rem;">
                        <strong style="color: var(--primary-text);">
                        {_('Правильные ответы')}:
                        </strong>
                    </div>
                    <div style="padding: 0.75rem; background: #d4edda;
                    border-radius: 0.375rem; color: #155724;">
                        {correct_list}
                    </div>
                </div>

                <div>
                    <div style="margin-bottom: 0.5rem;">
                        <strong style="color: var(--primary-text);">
                        {_('Выбранные ответы')}:
                        </strong>
                    </div>
                    <div style="padding: 0.75rem; background: #e2e3e5;
                    border-radius: 0.375rem; color: #383d41;">
                        {selected_list}
                    </div>
                </div>
            </div>

            {f'''
            <div style="margin-top: 1rem; margin-bottom: 1rem;">
                <div style="margin-bottom: 0.5rem;">
                    <strong style="color: #dc3545;">
                    {_('Ошибки')}:
                    </strong>
                </div>
                <div style="padding: 0.75rem; background: #f8d7da;
                border-radius: 0.375rem; color: #721c24;">
                    {missing_list}
                    {extra_list}
                </div>
            </div>
            ''' if missing_list or extra_list else ''}

            <div style="margin-top: 1rem; padding-top: 1rem;
            border-top: 1px solid var(--border-color);">
                <div style="display: flex; gap: 2rem;">
                    <div>
                        <strong>{_('Правильность')}:</strong>
                        {'✅' if obj.is_correct else '❌'}
                    </div>
                    <div>
                        <strong>{_('Получено баллов')}:</strong>
                        <span style="color: {'#198754'
        if obj.points_earned > 0 else '#dc3545'};
                        font-weight: 600;">
                            {obj.points_earned} / {obj.question.points}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        """
        return format_html(details_html)

    @action(description=_("Пересчитать правильность"), permissions=["change"])
    def recalculate_correctness(self, request, queryset):
        """Пересчитать правильность для выбранных ответов"""
        updated = 0
        for obj in queryset:
            old_correct = obj.is_correct
            obj.is_correct = obj.calculate_correctness()
            obj.points_earned = obj.calculate_points()

            if old_correct != obj.is_correct:
                obj.save(update_fields=["is_correct", "points_earned"])
                updated += 1

        self.message_user(
            request,
            _(f"Пересчитано {updated} ответов"),
            messages.SUCCESS,
        )

    actions = ["recalculate_correctness"]

    def get_queryset(self, request):
        """Оптимизация запросов"""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "user",
            "question",
            "question__module",
            "question__module__course",
        ).prefetch_related("selected_answers")


@admin.register(CodeSubmission)
class CodeSubmissionAdmin(ModelAdmin):
    """Админка для отправок решений"""

    list_display = (
        "public_id",
        "user_info",
        "challenge_link",
        "status_badge",
        "tests_result",
        "submitted_at",
    )
    list_filter = ("status", "submitted_at", "challenge")
    search_fields = (
        "user__email",
        "user__phone",
        "user__first_name",
        "user__last_name",
        "challenge__title",
    )
    list_per_page = 20
    ordering = ("-submitted_at",)
    readonly_fields = (
        "public_id",
        "code",
        "test_results",
        "submitted_at",
        "completed_at",
    )
    icon = "terminal"

    fieldsets = (
        (
            _("Информация"),
            {"fields": ("public_id", "user", "challenge", "status")},
        ),
        (_("Код"), {"fields": ("code",), "classes": ("wide",)}),
        (
            _("Результаты"),
            {"fields": ("tests_passed", "total_tests", "error_message")},
        ),
        (
            _("Детали тестов"),
            {"fields": ("test_results",), "classes": ("collapse",)},
        ),
        (
            _("Время"),
            {
                "fields": ("submitted_at", "completed_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @display(description=_("Пользователь"), ordering="user__email")
    def user_info(self, obj):
        url = reverse("admin:users_user_change", args=[obj.user.id])
        name = obj.user.get_full_name() or str(obj.user)
        return format_html('<a href="{}">{}</a>', url, name)

    @display(description=_("Задача"), ordering="challenge__title")
    def challenge_link(self, obj):
        url = reverse(
            "admin:content_codingchallenge_change", args=[obj.challenge.id]
        )
        return format_html('<a href="{}">{}</a>', url, obj.challenge.title)

    @display(description=_("Статус"))
    def status_badge(self, obj):
        colors = {
            "pending": "#6c757d",
            "running": "#0d6efd",
            "completed": "#198754",
            "error": "#dc3545",
            "timeout": "#fd7e14",
        }
        names = {
            "pending": _("В очереди"),
            "running": _("Выполняется"),
            "completed": _("Завершено"),
            "error": _("Ошибка"),
            "timeout": _("Таймаут"),
        }
        return format_html(
            '<span style="background: {}; color: white; '
            'padding: 2px 8px; border-radius: 12px;">{}</span>',
            colors.get(obj.status, "#6c757d"),
            names.get(obj.status, obj.status),
        )

    @display(description=_("Тесты"))
    def tests_result(self, obj):
        if obj.total_tests == 0:
            return "—"
        percent = (
            (obj.tests_passed / obj.total_tests) * 100
            if obj.total_tests > 0
            else 0
        )
        color = (
            "#198754"
            if percent == 100
            else "#ffc107" if percent > 0 else "#dc3545"
        )
        percent_label = f"{percent:.0f}"
        return format_html(
            '<span style="color: {};">{}/{} ({}%)</span>',
            color,
            obj.tests_passed,
            obj.total_tests,
            percent_label,
        )


@admin.register(LessonUserComment)
class LessonUserCommentAdmin(ModelAdmin):
    list_display = (
        "author_name",
        "lesson_kind",
        "lesson_public_id",
        "body_preview",
        "is_hidden",
        "created_at",
    )
    list_filter = ("lesson_kind", "is_hidden", "created_at")
    search_fields = (
        "body",
        "user__email",
        "user__first_name",
        "user__last_name",
        "lesson_public_id",
    )
    readonly_fields = ("public_id", "created_at", "updated_at")
    list_per_page = 30
    ordering = ("-created_at",)

    @admin.display(description=_("Автор"))
    def author_name(self, obj):
        return obj.user.get_full_name() or obj.user.email

    @admin.display(description=_("Текст"))
    def body_preview(self, obj):
        text = obj.body or ""
        return text[:80] + ("…" if len(text) > 80 else "")
