from django.core.management.base import BaseCommand
from projects.models import ProjectStage, TaskStatus, TaskPriority

class Command(BaseCommand):
    help = 'Initialize default project stages, task statuses and priorities'

    def handle(self, *args, **options):
        # Стадии проекта
        stages = [
            {'name': 'Планирование', 'order': 1, 'color': '#4a76a8'},
            {'name': 'Разработка', 'order': 2, 'color': '#2196F3'},
            {'name': 'Тестирование', 'order': 3, 'color': '#FF9800'},
            {'name': 'Внедрение', 'order': 4, 'color': '#4CAF50'},
            {'name': 'Завершен', 'order': 5, 'color': '#9E9E9E'},
        ]
        
        for stage_data in stages:
            stage, created = ProjectStage.objects.get_or_create(
                name=stage_data['name'],
                defaults=stage_data
            )
            if created:
                self.stdout.write(f'Created stage: {stage.name}')

        # Статусы задач
        statuses = [
            {'name': 'Новая', 'order': 1, 'color': '#4a76a8', 'is_default': True},
            {'name': 'В работе', 'order': 2, 'color': '#2196F3'},
            {'name': 'На проверке', 'order': 3, 'color': '#FF9800'},
            {'name': 'Завершена', 'order': 4, 'color': '#4CAF50', 'is_final': True},
            {'name': 'Отложена', 'order': 5, 'color': '#9E9E9E'},
        ]
        
        for status_data in statuses:
            status, created = TaskStatus.objects.get_or_create(
                name=status_data['name'],
                defaults=status_data
            )
            if created:
                self.stdout.write(f'Created status: {status.name}')

        # Приоритеты задач
        priorities = [
            {'name': 'Низкий', 'level': 1, 'color': '#4CAF50', 'icon': 'arrow-down'},
            {'name': 'Средний', 'level': 2, 'color': '#FF9800', 'icon': 'minus'},
            {'name': 'Высокий', 'level': 3, 'color': '#F44336', 'icon': 'arrow-up'},
            {'name': 'Критический', 'level': 4, 'color': '#9C27B0', 'icon': 'exclamation-triangle'},
        ]
        
        for priority_data in priorities:
            priority, created = TaskPriority.objects.get_or_create(
                name=priority_data['name'],
                defaults=priority_data
            )
            if created:
                self.stdout.write(f'Created priority: {priority.name}')

        self.stdout.write(self.style.SUCCESS('Successfully initialized statuses and priorities'))