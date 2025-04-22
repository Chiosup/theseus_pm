from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Project, Task
from .forms import ProjectForm, TaskForm
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
import openpyxl
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
@login_required

def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, creator=request.user)  # Только менеджер может редактировать
    
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project_list')
    else:
        form = ProjectForm(instance=project)

    return render(request, 'projects/edit_project.html', {'form': form, 'project': project})
@login_required
def project_list(request):
    """Отображение списка проектов, в которых участвует пользователь или которые он создал."""
    if request.user.is_superuser:
        projects = Project.objects.all()  # Админ видит все проекты
    elif request.user.groups.filter(name="Менеджеры").exists():
        projects = Project.objects.filter(creator=request.user)  # Менеджеры видят свои проекты
    else:
        projects = Project.objects.filter(participants=request.user)  # Остальные видят, где участвуют

    # Добавляем атрибут с количеством завершенных задач
    for project in projects:
        project.completed_tasks_count = project.tasks.filter(status="completed").count()

    return render(request, "projects/project_list.html", {"projects": projects})

@login_required
def project_detail(request, project_id):
    """Отображение деталей проекта и списка задач в нем."""
    project = get_object_or_404(Project, id=project_id)
    tasks = project.tasks.all().order_by("due_date")

    tasks_data = []
    for task in tasks:
        tasks_data.append({
            "id": task.id,
            "name": task.title,
            "start": task.start_date.strftime("%Y-%m-%d") if task.start_date else None,
            "end": task.end_date.strftime("%Y-%m-%d") if task.end_date else None,
            "progress": 100 if task.status == "done" else (50 if task.status == "in_progress" else 0)
        })

    tasks_json = json.dumps(tasks_data, ensure_ascii=False)  # Генерация JSON

    print("DEBUG JSON:", tasks_json)  # Выведи в консоль сервера для отладки

    return render(request, 'projects/project_detail.html', {
        "project": project,
        "tasks": tasks,  # Передаем задачи для списка
        "tasks_json": tasks_json  # Передаем JSON для диаграммы Ганта
    })

@login_required
@require_http_methods(["GET", "POST"])
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.creator = request.user
            project.save()
            form.save_m2m()  # Для ManyToMany поля participants
            
            return JsonResponse({
                'success': True,
                'project': {
                    'id': project.id,
                    'title': project.title,
                    'description': project.description,
                }
            })
        else:
            form_html = render_to_string('projects/project_form.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'form_html': form_html})
    
    # GET запрос
    form = ProjectForm()
    form_html = render_to_string('projects/project_form.html', {'form': form}, request=request)
    return JsonResponse({'form_html': form_html})

def create_task_modal(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            form.save_m2m()  # сохраняем связи
            return JsonResponse({'success': True})
        else:
            html = render(request, 'projects/partials/task_form.html', {'form': form, 'project': project}).content.decode('utf-8')
            return JsonResponse({'success': False, 'form_html': html})
    else:
        form = TaskForm()
        html = render(request, 'projects/partials/task_form.html', {'form': form, 'project': project}).content.decode('utf-8')
        return JsonResponse({'form_html': html})


@login_required
def update_task_status(request, task_id):
    """Обновление статуса задачи (только для исполнителей задачи)."""
    task = get_object_or_404(Task, id=task_id)

    if request.user not in task.assignee.all():
        return redirect('project_detail', project_id=task.project.id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in ['new', 'in_progress', 'done']:
            task.status = new_status
            if new_status == 'done':
                task.completed_by = request.user
            task.save()
    
    return redirect('project_detail', project_id=task.project.id)
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    return render(request, "projects/task_detail.html", {"task": task})

@login_required
def start_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if task.status == "new":
        task.status = "in_progress"
        task.save()
    return redirect("project_detail", project_id=task.project.id)

@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if task.status == "in_progress":
        task.status = "done"
        task.save()
    return redirect("project_detail", project_id=task.project.id)
def revert_to_pending(request, task_id):
    """Откатывает задачу из 'in_progress' обратно в 'pending'."""
    task = get_object_or_404(Task, id=task_id)
    if task.status == 'in_progress':  
        task.status = 'new'
        task.save()
    return redirect('task_detail', task_id=task.id)

def revert_to_in_progress(request, task_id):
    """Откатывает задачу из 'completed' обратно в 'in_progress'."""
    task = get_object_or_404(Task, id=task_id)
    if task.status == 'done':  
        task.status = 'in_progress'
        task.save()
    return redirect('task_detail', task_id=task.id)
def create_task(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            form.save_m2m()  # Если есть ManyToMany-поля (например, assigned_to)
            return redirect('task_detail', task_id=task.id)  # Или другой редирект
    else:
        form = TaskForm()
    
    return render(request, 'projects/task_form.html', {
        'form': form,
        'project': project,  # Передаем проект в шаблон
    })

def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('task_detail', task_id=task.id)
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'projects/task_form.html', {
        'form': form,
        'task': task,  # Передаем задачу в шаблон
    })
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    project_id = task.project.id
    
    if request.method == 'POST':
        task.delete()
        return redirect('project_detail', project_id=project_id)
    
    # Для GET-запросов можно вернуть на страницу задачи
    return redirect('task_detail', task_id=task_id)
@login_required
@require_http_methods(["POST"])
@csrf_exempt

def update_task_status_ajax(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        
        # Проверка прав
        has_permission = (
            request.user in task.assigned_to.all() or
            request.user == task.project.creator or
            request.user.is_superuser
        )
        
        if not has_permission:
            return JsonResponse({'error': 'У вас нет прав для изменения этой задачи'}, status=403)
        
        data = json.loads(request.body)
        new_status = data.get('status')
        
        # Проверка допустимых статусов
        valid_statuses = ['new', 'in_progress', 'done']
        if new_status not in valid_statuses:
            return JsonResponse(
                {'error': f'Недопустимый статус задачи. Допустимые: {", ".join(valid_statuses)}'}, 
                status=400
            )
        
        # Обновление только статуса (без изменения дат)
        task.status = new_status
        task.save()
        
        return JsonResponse({
            'success': True,
            'new_status': task.status,
            'status_display': task.get_status_display(),
            'start_date': task.start_date.strftime('%Y-%m-%d') if task.start_date else None,
            'end_date': task.end_date.strftime('%Y-%m-%d') if task.end_date else None
        })
    
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Задача не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


User = get_user_model()

def employee_list(request):
    employees = User.objects.all().order_by('last_name', 'first_name')
    
    employee_data = []
    for employee in employees:
        # Получаем все задачи сотрудника
        tasks = Task.objects.filter(assigned_to=employee)
        
        # Считаем количество задач по статусам
        total_tasks = tasks.count()
        active_tasks = tasks.filter(status='in_progress').count()
        
        # Вычисляем процент загрузки
        progress = 0
        if total_tasks > 0:
            progress = (active_tasks / total_tasks) * 100

        task_counts = {
            'total': total_tasks,
            'new': tasks.filter(status='new').count(),
            'in_progress': active_tasks,
            'done': tasks.filter(status='done').count(),
            'overdue': tasks.filter(due_date__lt=timezone.now().date(), status__in=['new', 'in_progress']).count()
        }
        
        # Получаем проекты сотрудника
        projects = employee.projects.all().distinct()
        
        employee_data.append({
            'employee': employee,
            'task_counts': task_counts,
            'projects': projects,
            'progress': progress,  # Добавляем вычисленный прогресс
            'overdue_tasks': tasks.filter(due_date__lt=timezone.now().date(), status__in=['new', 'in_progress']),
            'all_tasks': tasks
        })
    
    return render(request, 'projects/employee_list.html', {
        'employee_data': employee_data,
        'today': timezone.now().date()
    })