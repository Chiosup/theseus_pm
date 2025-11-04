from django.contrib import admin
from .models import Project, Task
# Register your models here.

from django.contrib import admin
from .models import Project, Task, ProjectStage, TaskStatus, TaskPriority

@admin.register(ProjectStage)
class ProjectStageAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'color', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']

@admin.register(TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'color', 'is_default', 'is_final', 'is_active']
    list_editable = ['order', 'is_default', 'is_final', 'is_active']
    list_filter = ['is_active', 'is_default']

@admin.register(TaskPriority)
class TaskPriorityAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'color', 'is_active']
    list_editable = ['level', 'is_active']
    list_filter = ['is_active']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'version', 'stage', 'status', 'creator', 'start_date']
    list_filter = ['stage', 'status']
    filter_horizontal = ['available_statuses', 'participants']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'status', 'priority', 'due_date']
    list_filter = ['status', 'priority', 'project']