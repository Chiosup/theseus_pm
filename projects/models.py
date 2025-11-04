from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ProjectStage(models.Model):
    """Стадии проекта"""
    name = models.CharField(max_length=100, verbose_name="Название стадии")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    color = models.CharField(max_length=7, default='#4a76a8', verbose_name="Цвет")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    
    class Meta:
        verbose_name = "Стадия проекта"
        verbose_name_plural = "Стадии проекта"
        ordering = ['order']
    
    def __str__(self):
        return self.name

class TaskStatus(models.Model):
    """Статусы задач"""
    name = models.CharField(max_length=100, verbose_name="Название статуса")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    color = models.CharField(max_length=7, default='#4a76a8', verbose_name="Цвет")
    is_default = models.BooleanField(default=False, verbose_name="Статус по умолчанию")
    is_final = models.BooleanField(default=False, verbose_name="Финальный статус")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    class Meta:
        verbose_name = "Статус задачи"
        verbose_name_plural = "Статусы задач"
        ordering = ['order']
    
    def __str__(self):
        return self.name

class TaskPriority(models.Model):
    """Приоритеты задач"""
    name = models.CharField(max_length=100, verbose_name="Название приоритета")
    level = models.IntegerField(default=0, verbose_name="Уровень приоритета")
    color = models.CharField(max_length=7, default='#4a76a8', verbose_name="Цвет")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Иконка")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    class Meta:
        verbose_name = "Приоритет задачи"
        verbose_name_plural = "Приоритеты задач"
        ordering = ['level']
    
    def __str__(self):
        return self.name

class Project(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания", null=True, blank=True)
    
    # Заменяем старые CHOICES на связи с новыми моделями
    stage = models.ForeignKey(ProjectStage, on_delete=models.SET_NULL, null=True, blank=True, 
                             verbose_name="Стадия проекта")
    status = models.CharField(max_length=20, choices=[
        ('active', 'Активный'),
        ('completed', 'Завершен'),
    ], default='active', verbose_name="Статус")
    
    version = models.CharField(max_length=20, default='v1.0', verbose_name="Версия проекта")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_projects", verbose_name="Создатель")
    participants = models.ManyToManyField(User, related_name="projects", verbose_name="Участники")
    
    # Статусы, которые используются в этом проекте
    available_statuses = models.ManyToManyField(TaskStatus, blank=True, verbose_name="Доступные статусы")
    
    def get_project_statuses(self):
        """Получить статусы, выбранные для этого проекта"""
        if self.available_statuses.exists():
            return self.available_statuses.filter(is_active=True).order_by('order')
        else:
            # Возвращаем все активные статусы по умолчанию
            return TaskStatus.objects.filter(is_active=True).order_by('order')
    
    def get_default_status(self):
        """Получить статус по умолчанию для проекта"""
        statuses = self.get_project_statuses()
        default_status = statuses.filter(is_default=True).first()
        if not default_status:
            default_status = statuses.first()
        return default_status
    
    def __str__(self):
        return f"{self.title} ({self.version})"
    
    def can_create(self, user):
        return user.role == 'manager'
    
    def get_available_statuses(self):
        """Получить доступные статусы для проекта"""
        if self.available_statuses.exists():
            return self.available_statuses.filter(is_active=True)
        return TaskStatus.objects.filter(is_active=True)
    
    def get_default_status(self):
        """Получить статус по умолчанию"""
        default_status = self.get_available_statuses().filter(is_default=True).first()
        if not default_status:
            default_status = self.get_available_statuses().first()
        return default_status

class Task(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    due_date = models.DateField(verbose_name="Срок выполнения")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Заменяем старые CHOICES на связи с новыми моделями
    status = models.ForeignKey(TaskStatus, on_delete=models.SET_NULL, null=True, 
                              verbose_name="Статус")
    priority = models.ForeignKey(TaskPriority, on_delete=models.SET_NULL, null=True,
                                verbose_name="Приоритет")
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks", verbose_name="Проект")
    assigned_to = models.ManyToManyField(User, related_name="tasks", verbose_name="Исполнители")
    previous_task = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name="next_task", verbose_name="Предыдущая задача")
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='subtasks', verbose_name="Родительская задача")
    
    # НОВЫЕ ПОЛЯ ДЛЯ КАНБАН-ДОСКИ ПОДЗАДАЧ
    has_kanban = models.BooleanField(default=False, verbose_name="Использовать канбан-доску для подзадач")
    subtask_statuses = models.ManyToManyField(TaskStatus, blank=True, 
                                             related_name='kanban_tasks',
                                             verbose_name="Статусы для подзадач")
    
    def __str__(self):
        return self.title
    
    def can_create(self, user):
        return user.role == 'manager'
    
    def save(self, *args, **kwargs):
        # Устанавливаем статус по умолчанию при создании
        if not self.status_id and self.project:
            default_status = self.project.get_default_status()
            if default_status:
                self.status = default_status
        super().save(*args, **kwargs)
    
    def get_subtasks(self):
        """Получить подзадачи"""
        return self.subtasks.all()
    
    def is_subtask(self):
        """Проверить, является ли задача подзадачей"""
        return self.parent_task is not None
    
    def get_available_statuses(self):
        """Получить доступные статусы для подзадач"""
        if self.subtask_statuses.exists():
            return self.subtask_statuses.filter(is_active=True).order_by('order')
        else:
            # По умолчанию используем все активные статусы
            return TaskStatus.objects.filter(is_active=True).order_by('order')

class SubTask(models.Model):
    """Подзадачи"""
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание", blank=True)
    due_date = models.DateField(verbose_name="Срок выполнения", null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    status = models.ForeignKey(TaskStatus, on_delete=models.SET_NULL, null=True, 
                              verbose_name="Статус")
    priority = models.ForeignKey(TaskPriority, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name="Приоритет")
    
    parent_task = models.ForeignKey(Task, on_delete=models.CASCADE, 
                                   related_name='subtasks_list', verbose_name="Родительская задача")
    assigned_to = models.ManyToManyField(User, related_name="subtasks", verbose_name="Исполнители", blank=True)
    
    order = models.IntegerField(default=0, verbose_name="Порядок")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Подзадача"
        verbose_name_plural = "Подзадачи"
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.title} (подзадача {self.parent_task.title})"
    
    def get_available_statuses(self):
        """Получить доступные статусы для подзадачи"""
        return self.parent_task.get_available_statuses()
    
    def get_default_status(self):
        """Получить статус по умолчанию"""
        statuses = self.get_available_statuses()
        default_status = statuses.filter(is_default=True).first()
        if not default_status:
            default_status = statuses.first()
        return default_status
    
    def save(self, *args, **kwargs):
        # Устанавливаем статус по умолчанию при создании
        if not self.status_id:
            default_status = self.get_default_status()
            if default_status:
                self.status = default_status
        super().save(*args, **kwargs)