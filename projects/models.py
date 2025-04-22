from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Project(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('completed', 'Завершен'),
    ]

    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Статус")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_projects", verbose_name="Создатель")
    participants = models.ManyToManyField(User, related_name="projects", verbose_name="Участники")
    def can_create(self, user):
        return user.role == 'manager'
    def __str__(self):
        return self.title

class Task(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В процессе'),
        ('done', 'Выполнена'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]

    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    due_date = models.DateField(verbose_name="Срок выполнения")
    start_date = models.DateField(null=True, blank=True)  # Дата начала
    end_date = models.DateField(null=True, blank=True)  # Дата завершения
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name="Приоритет")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks", verbose_name="Проект")
    assigned_to = models.ManyToManyField(User, related_name="tasks", verbose_name="Исполнители")
    previous_task = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="next_task", verbose_name="Предыдущая задача")
    def can_create(self, user):
            return user.role == 'manager'
    def __str__(self):
        return self.title