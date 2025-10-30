from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Sub


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name',
        'get_avatar_preview', 'is_staff', 'is_active'
    )
    list_display_links = ('id', 'username', 'email')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    ordering = ('email',)

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Персональная информация', {
            'fields': ('email', 'first_name', 'last_name', 'avatar', 'get_avatar_preview')
        }),
        ('Разрешения', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Важные даты', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('get_avatar_preview', 'last_login', 'date_joined')
    filter_horizontal = ('groups', 'user_permissions')

    def get_avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 50%;" />',
                obj.avatar.url
            )
        return "Аватар не установлен"

    get_avatar_preview.short_description = 'Предпросмотр аватара'


class SubscriptionInline(admin.TabularInline):
    model = Sub
    fk_name = 'user'
    extra = 1
    verbose_name = "Подписка"
    verbose_name_plural = "Мои подписки"


class SubscriberInline(admin.TabularInline):
    model = Sub
    fk_name = 'subscribed_to'
    extra = 1
    verbose_name = "Подписчик"
    verbose_name_plural = "Мои подписчики"


@admin.register(Sub)
class SubAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'subscribed_to', 'get_user_email', 'get_author_email')
    list_display_links = ('id', 'user')
    search_fields = (
        'user__username', 'user__email',
        'subscribed_to__username', 'subscribed_to__email'
    )
    list_filter = ('user', 'subscribed_to')
    ordering = ('user',)

    def get_user_email(self, obj):
        return obj.user.email

    get_user_email.short_description = 'Email подписчика'

    def get_author_email(self, obj):
        return obj.subscribed_to.email

    get_author_email.short_description = 'Email автора'


# Добавляем inline в админку пользователя
CustomUserAdmin.inlines = [SubscriptionInline, SubscriberInline]