from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email')}),
        ('Роли и доступ', {'fields': ('role', 'groups', 'user_permissions', 'is_staff', 'is_active', 'is_superuser')}),  # Добавил groups
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'groups', 'is_staff', 'is_active')}  # Добавил groups
        ),
    )

    search_fields = ('username', 'email')
    filter_horizontal = ('groups', 'user_permissions')  # Оставляем
    ordering = ('username',)

    def has_module_permission(self, request):
        """Ограничиваем доступ к админке"""
        return request.user.is_superuser  # Только суперпользователи могут заходить

admin.site.register(CustomUser, CustomUserAdmin)
