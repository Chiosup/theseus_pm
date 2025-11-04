from django import template

register = template.Library()

@register.filter
def filter_status(tasks, status_id):
    """Фильтрует задачи по статусу"""
    return [task for task in tasks if task.status and task.status.id == status_id]