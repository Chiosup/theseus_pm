from django import forms
from .models import Project, Task, ProjectStage, TaskStatus, TaskPriority

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'start_date', 'end_date', 'stage', 'status', 
                 'version', 'participants', 'available_statuses']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название проекта'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опишите детали проекта'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'stage': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'v1.0'
            }),
            'participants': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': 5
            }),
            'available_statuses': forms.CheckboxSelectMultiple(attrs={
                'class': 'status-checkboxes'
            }),
        }
        labels = {
            'available_statuses': 'Статусы задач для проекта'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем только активные стадии и статусы
        self.fields['stage'].queryset = ProjectStage.objects.filter(is_active=True)
        self.fields['available_statuses'].queryset = TaskStatus.objects.filter(is_active=True)
        
        if not self.instance.pk:
            self.fields['version'].initial = 'v1.0'
            # Устанавливаем все активные статусы по умолчанию
            default_statuses = TaskStatus.objects.filter(is_active=True)
            self.fields['available_statuses'].initial = default_statuses
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'start_date', 'end_date', 'due_date', 
                 'status', 'priority', 'assigned_to', 'previous_task', 'parent_task']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'previous_task': forms.Select(attrs={'class': 'form-control'}),
            'parent_task': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        if self.project:
            # Ограничиваем выбор статусов только теми, что выбраны для проекта
            self.fields['status'].queryset = self.project.get_project_statuses()
            self.fields['previous_task'].queryset = Task.objects.filter(project=self.project)
            self.fields['parent_task'].queryset = Task.objects.filter(project=self.project)
        
        # Фильтруем только активные приоритеты
        self.fields['priority'].queryset = TaskPriority.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        
        if not start_date:
            from django.utils.timezone import now
            cleaned_data["start_date"] = now().date()
        if not end_date:
            from datetime import timedelta
            cleaned_data["end_date"] = cleaned_data["start_date"] + timedelta(days=7)
        
        cleaned_data["due_date"] = cleaned_data["end_date"]
        return cleaned_data