from django import forms
from .models import Project, Task

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'start_date', 'end_date', 'status', 'participants']
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
            'status': forms.Select(attrs={'class': 'form-control'}),
            'participants': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': 5
            }),
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'start_date', 'end_date', 'due_date', 'status', 'priority', 'assigned_to', 'previous_task']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'readonly': 'readonly'}),  # Запрет изменения вручную
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date") or now().date()
        end_date = cleaned_data.get("end_date") or (start_date + timedelta(days=7))
        
        # Устанавливаем даты по умолчанию, если их нет
        cleaned_data["start_date"] = start_date
        cleaned_data["end_date"] = end_date
        cleaned_data["due_date"] = end_date  # Автоматически устанавливаем срок выполнения

        return cleaned_data