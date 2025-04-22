from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('director', 'Руководитель'),
        ('manager', 'Менеджер'),
        ('employee', 'Сотрудник'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')
    
    def save(self, *args, **kwargs):
        """Автоматически задаем is_staff и is_superuser в зависимости от роли"""
        if self.role in ['admin', 'director']:
            self.is_staff = True
            self.is_superuser = True  # Администраторы и руководители имеют полный доступ
        else:
            self.is_staff = False  # Запрещаем доступ к админке для менеджеров и сотрудников
            self.is_superuser = False
        super().save(*args, **kwargs)
    def get_full_name(self):
        """Возвращает полное имя пользователя"""
        full_name = f"{self.last_name} {self.first_name}".strip()
        return full_name if full_name else self.username