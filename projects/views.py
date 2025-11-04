from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Project, Task, TaskStatus, TaskPriority, ProjectStage, SubTask
from .forms import ProjectForm, TaskForm, SubTaskForm
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

   
    for project in projects:
        project.completed_tasks_count = project.tasks.filter(status="completed").count()

    return render(request, "projects/project_list.html", {"projects": projects})
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def update_task_status(request, task_id):
    """Обновление статуса задачи через drag&drop"""
    try:
        task = get_object_or_404(Task, id=task_id)
        
        # Проверяем права - пользователь должен быть участником проекта или создателем
        if request.user not in task.project.participants.all() and request.user != task.project.creator:
            return JsonResponse({'error': 'Нет прав на изменение задачи'}, status=403)
        
        # Парсим JSON данные
        data = json.loads(request.body)
        new_status_id = data.get('status_id')
        
        if not new_status_id:
            return JsonResponse({'error': 'Не указан статус'}, status=400)
        
        # Находим новый статус
        try:
            new_status = TaskStatus.objects.get(id=new_status_id)
        except TaskStatus.DoesNotExist:
            return JsonResponse({'error': 'Статус не найден'}, status=400)
        
        # Проверяем, что статус доступен для этого проекта
        if new_status not in task.project.get_project_statuses():
            return JsonResponse({'error': 'Статус недоступен для этого проекта'}, status=400)
        
        # Обновляем статус
        old_status = task.status
        task.status = new_status
        
        # Автоматически обновляем даты при изменении статуса
        from django.utils import timezone
        
        if new_status.name == 'В работе' and not task.start_date:
            task.start_date = timezone.now().date()
        
        if new_status.name == 'Завершена' and not task.end_date:
            task.end_date = timezone.now().date()
        
        task.save()
        
        # Возвращаем обновленные данные
        response_data = {
            'success': True,
            'task_id': task.id,
            'status_name': task.status.name,
            'start_date': task.start_date.isoformat() if task.start_date else None,
            'end_date': task.end_date.isoformat() if task.end_date else None,
        }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат данных'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    tasks = project.tasks.all().select_related('status').prefetch_related('assigned_to')
    
    # Получаем статусы, выбранные для этого проекта
    project_statuses = project.get_project_statuses()
    
    # Готовим данные для диаграммы Ганта
    tasks_data = []
    for task in tasks:
        task_data = {
            'id': str(task.id),
            'name': task.title,
            'start': task.start_date.isoformat() if task.start_date else None,
            'end': task.end_date.isoformat() if task.end_date else None,
            'status': task.status.name if task.status else 'Без статуса'
        }
        tasks_data.append(task_data)
    
    context = {
        'project': project,
        'tasks': tasks,
        'project_statuses': project_statuses,  # Добавляем статусы проекта
        'tasks_json': json.dumps(tasks_data),
    }
    
    return render(request, 'projects/project_detail.html', context)
@login_required
@require_http_methods(["GET", "POST"])
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.creator = request.user
            project.save()
            form.save_m2m()  
            
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
@require_http_methods(["POST"])
@login_required
def complete_subtask(request, subtask_id):
    """Завершение подзадачи"""
    subtask = get_object_or_404(SubTask, id=subtask_id)
    
    # Проверяем права
    if request.user not in subtask.assigned_to.all():
        return JsonResponse({'success': False, 'error': 'У вас нет прав на завершение этой подзадачи'})
    
    # Находим статус "Завершена"
    try:
        done_status = TaskStatus.objects.get(name='Завершена')
        subtask.status = done_status
        subtask.end_date = timezone.now().date()
        subtask.save()
        return JsonResponse({'success': True})
    except TaskStatus.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Статус "Завершена" не найден'})

@require_http_methods(["POST"])
@login_required
def reopen_subtask(request, subtask_id):
    """Переоткрытие подзадачи"""
    subtask = get_object_or_404(SubTask, id=subtask_id)
    
    # Проверяем права
    if (request.user not in subtask.assigned_to.all() and 
        request.user.role not in ['admin', 'director']):
        return JsonResponse({'success': False, 'error': 'У вас нет прав на переоткрытие этой подзадачи'})
    
    # Находим статус "В работе" или первый доступный статус
    try:
        in_progress_status = TaskStatus.objects.get(name='В работе')
        subtask.status = in_progress_status
        subtask.end_date = None
        subtask.save()
        return JsonResponse({'success': True})
    except TaskStatus.DoesNotExist:
        # Используем первый доступный статус
        available_status = subtask.get_available_statuses().first()
        if available_status:
            subtask.status = available_status
            subtask.end_date = None
            subtask.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Нет доступных статусов'})
@login_required
def task_detail(request, task_id):
    """Детальная страница задачи"""
    task = get_object_or_404(Task, id=task_id)
    
    # Проверяем права доступа
    if (request.user not in task.project.participants.all() and 
        request.user != task.project.creator and 
        not request.user.is_superuser):
        return HttpResponseForbidden("У вас нет доступа к этой задаче")
    
    # Получаем подзадачи
    subtasks = task.subtasks_list.all()
    
    # Получаем статусы для канбан-доски подзадач
    subtask_statuses = task.get_available_statuses()
    
    context = {
        'task': task,
        'subtasks': subtasks,
        'subtask_statuses': subtask_statuses,  # Добавляем статусы для канбана
        'project': task.project,
    }
    
    return render(request, 'projects/task_detail.html', context)

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
            form.save_m2m() 
            return redirect('task_detail', task_id=task.id)  
    else:
        form = TaskForm()
    
    return render(request, 'projects/task_form.html', {
        'form': form,
        'project': project,  # Передаем проект в шаблон
    })

@login_required
def edit_task(request, task_id):
    """Редактирование задачи через модальное окно"""
    task = get_object_or_404(Task, id=task_id)
    
    # Проверяем права
    if (request.user not in task.assigned_to.all() and 
        request.user != task.project.creator and 
        request.user.role not in ['admin', 'director']):
        return JsonResponse({'success': False, 'error': 'У вас нет прав на редактирование этой задачи'})
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, project=task.project)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            form_html = render_to_string('projects/task_form.html', {'form': form, 'task': task}, request=request)
            return JsonResponse({'success': False, 'form_html': form_html})
    else:
        form = TaskForm(instance=task, project=task.project)
        form_html = render_to_string('projects/task_form.html', {'form': form, 'task': task}, request=request)
        return JsonResponse({'form_html': form_html})

@require_http_methods(["POST"])
@login_required
def complete_task(request, task_id):
    """Завершение задачи"""
    task = get_object_or_404(Task, id=task_id)
    
    # Проверяем права
    if request.user not in task.assigned_to.all():
        return JsonResponse({'success': False, 'error': 'У вас нет прав на завершение этой задачи'})
    
    # Находим статус "Завершена"
    try:
        done_status = TaskStatus.objects.get(name='Завершена')
        task.status = done_status
        task.end_date = timezone.now().date()
        task.save()
        return JsonResponse({'success': True})
    except TaskStatus.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Статус "Завершена" не найден'})

@require_http_methods(["POST"])
@login_required
def reopen_task(request, task_id):
    """Переоткрытие задачи"""
    task = get_object_or_404(Task, id=task_id)
    
    # Проверяем права
    if (request.user not in task.assigned_to.all() and 
        request.user.role not in ['admin', 'director']):
        return JsonResponse({'success': False, 'error': 'У вас нет прав на переоткрытие этой задачи'})
    
    # Находим статус "В работе" или первый доступный статус
    try:
        in_progress_status = TaskStatus.objects.get(name='В работе')
        task.status = in_progress_status
        task.end_date = None
        task.save()
        return JsonResponse({'success': True})
    except TaskStatus.DoesNotExist:
        # Используем первый доступный статус
        available_status = task.project.get_project_statuses().first()
        if available_status:
            task.status = available_status
            task.end_date = None
            task.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Нет доступных статусов'})
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    project_id = task.project.id
    
    if request.method == 'POST':
        task.delete()
        return redirect('project_detail', project_id=project_id)
    
    # Для GET-запросов можно вернуть на страницу задачи
    return redirect('task_detail', task_id=task_id)
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def update_task_status(request, task_id):
    """Обновление статуса задачи через drag&drop"""
    print(f"=== UPDATE TASK STATUS CALLED ===")
    print(f"Task ID: {task_id}")
    print(f"User: {request.user}")
    
    try:
        task = get_object_or_404(Task, id=task_id)
        print(f"Task found: {task.title}")
        
        # ПРАВИЛЬНАЯ ПРОВЕРКА ПРАВ - используем assigned_to вместо assignee
        if (request.user not in task.assigned_to.all() and 
            request.user != task.project.creator and
            request.user not in task.project.participants.all()):
            print("Permission denied")
            return JsonResponse({'error': 'Нет прав на изменение задачи'}, status=403)
        
        # Парсим JSON данные
        data = json.loads(request.body)
        new_status_id = data.get('status_id')
        print(f"New status ID: {new_status_id}")
        
        if not new_status_id:
            print("No status ID provided")
            return JsonResponse({'error': 'Не указан статус'}, status=400)
        
        # Находим новый статус
        try:
            new_status = TaskStatus.objects.get(id=new_status_id)
            print(f"New status found: {new_status.name}")
        except TaskStatus.DoesNotExist:
            print("Status not found")
            return JsonResponse({'error': 'Статус не найден'}, status=400)
        
        # Проверяем, что статус доступен для этого проекта
        project_statuses = task.project.get_project_statuses()
        if new_status not in project_statuses:
            print("Status not available for project")
            return JsonResponse({'error': 'Статус недоступен для этого проекта'}, status=400)
        
        # Обновляем статус
        old_status_name = task.status.name if task.status else "None"
        task.status = new_status
        print(f"Status changed from {old_status_name} to {new_status.name}")
        
        # Автоматически обновляем даты при изменении статуса
        from django.utils import timezone
        
        if new_status.name == 'В работе' and not task.start_date:
            task.start_date = timezone.now().date()
            print("Start date set")
        
        if new_status.name == 'Завершена' and not task.end_date:
            task.end_date = timezone.now().date()
            print("End date set")
        
        task.save()
        print("Task saved successfully")
        
        # Возвращаем обновленные данные
        response_data = {
            'success': True,
            'task_id': task.id,
            'status_name': task.status.name,
            'start_date': task.start_date.isoformat() if task.start_date else None,
            'end_date': task.end_date.isoformat() if task.end_date else None,
        }
        
        print(f"Response: {response_data}")
        return JsonResponse(response_data)
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return JsonResponse({'error': 'Неверный формат данных'}, status=400)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
User = get_user_model()

def employee_list(request):
    employees = User.objects.all().order_by('last_name', 'first_name')
    employee_data = []
    
    for employee in employees:
        tasks = Task.objects.filter(assigned_to=employee)
        total_tasks = tasks.count()
        
        # Группируем задачи по статусам
        status_counts = {}
        for task in tasks:
            status_name = task.status.name if task.status else 'Без статуса'
            status_counts[status_name] = status_counts.get(status_name, 0) + 1
        
        # Определяем активные задачи (не финальные статусы)
        active_tasks_count = 0
        if TaskStatus.objects.filter(is_final=True).exists():
            final_statuses = TaskStatus.objects.filter(is_final=True)
            active_tasks_count = tasks.exclude(status__in=final_statuses).count()
        else:
            # Fallback: считаем все задачи кроме "Завершена" активными
            active_tasks_count = tasks.exclude(status__name='Завершена').count()
        
        # Расчет прогресса
        progress = 0
        if total_tasks > 0:
            progress = (active_tasks_count / total_tasks) * 100
        
        # Подсчет просроченных задач
        overdue_tasks = tasks.filter(
            due_date__lt=timezone.now().date()
        ).exclude(
            status__is_final=True
        ).count()
        
        # Получаем основные статусы для отображения
        new_count = status_counts.get('Новая', 0)
        in_progress_count = status_counts.get('В работе', 0)
        done_count = status_counts.get('Завершена', 0)
        
        task_counts = {
            'total': total_tasks,
            'new': new_count,
            'in_progress': in_progress_count,
            'done': done_count,
            'overdue': overdue_tasks,
            'status_counts': status_counts,  # Все статусы для отладки
        }
        
        projects = employee.projects.all().distinct()
        
        employee_data.append({
            'employee': employee,
            'task_counts': task_counts,
            'projects': projects,
            'progress': progress,
            'all_tasks': tasks,
        })
    
    return render(request, 'projects/employee_list.html', {
        'employee_data': employee_data,
        'today': timezone.now().date()
    })
@login_required
def edit_project(request, project_id):
    """Редактирование проекта"""
    project = get_object_or_404(Project, id=project_id)
    
    # Проверяем права на редактирование
    if not (request.user == project.creator or request.user.role in ['admin', 'director']):
        return JsonResponse({'success': False, 'error': 'Нет прав на редактирование'})
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            form_html = render_to_string('projects/project_form.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'form_html': form_html})
    
    # GET запрос - возвращаем форму
    form = ProjectForm(instance=project)
    form_html = render_to_string('projects/project_form.html', {'form': form}, request=request)
    return JsonResponse({'form_html': form_html})
@login_required
def duplicate_project(request, project_id):
    """Создание копии проекта со всеми задачами"""
    original_project = get_object_or_404(Project, id=project_id)
    
    # Проверяем права на копирование
    if not (request.user.role in ['admin', 'director', 'manager']):
        return JsonResponse({'success': False, 'error': 'Нет прав на копирование проектов'})
    
    try:
        # Создаем копию проекта
        duplicated_project = Project.objects.create(
            title=f"{original_project.title} (Копия)",
            description=original_project.description,
            start_date=original_project.start_date,
            end_date=original_project.end_date,
            status='active',  # Все копии становятся активными
            version=original_project.version,
            creator=request.user
        )
        
        # Копируем участников
        duplicated_project.participants.set(original_project.participants.all())
        
        # Копируем задачи
        task_mapping = {}  # Для отслеживания связи между оригинальными и скопированными задачами
        
        for original_task in original_project.tasks.all():
            duplicated_task = Task.objects.create(
                title=original_task.title,
                description=original_task.description,
                due_date=original_task.due_date,
                start_date=original_task.start_date,
                end_date=original_task.end_date,
                status='new',  # Все скопированные задачи становятся новыми
                priority=original_task.priority,
                project=duplicated_project
            )
            
            # Копируем исполнителей
            duplicated_task.assigned_to.set(original_task.assigned_to.all())
            
            # Сохраняем связь для обработки предыдущих задач
            task_mapping[original_task.id] = duplicated_task
        
        # Обновляем связи между задачами (previous_task)
        for original_task in original_project.tasks.all():
            if original_task.previous_task:
                duplicated_task = task_mapping[original_task.id]
                duplicated_previous_task = task_mapping.get(original_task.previous_task.id)
                if duplicated_previous_task:
                    duplicated_task.previous_task = duplicated_previous_task
                    duplicated_task.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Проект "{original_project.title}" успешно скопирован',
            'new_project_id': duplicated_project.id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
        
        
    
@login_required
def subtask_detail(request, subtask_id):
    """Детальная страница подзадачи"""
    subtask = get_object_or_404(SubTask, id=subtask_id)
    
    # Проверяем права доступа
    if (request.user not in subtask.parent_task.assigned_to.all() and 
        request.user != subtask.parent_task.project.creator and 
        not request.user.is_superuser):
        return HttpResponseForbidden("У вас нет доступа к этой подзадаче")
    
    context = {
        'subtask': subtask,
        'task': subtask.parent_task,
        'project': subtask.parent_task.project,
    }
    
    return render(request, 'projects/subtask_detail.html', context)

@login_required
def create_subtask_modal(request, task_id):
    """Создание подзадачи через модальное окно"""
    task = get_object_or_404(Task, pk=task_id)
    
    # Проверяем права
    if (request.user not in task.assigned_to.all() and 
        request.user != task.project.creator and 
        request.user.role not in ['admin', 'director']):
        return JsonResponse({'success': False, 'error': 'Нет прав на создание подзадач'})
    
    if request.method == 'POST':
        form = SubTaskForm(request.POST, parent_task=task)
        if form.is_valid():
            subtask = form.save(commit=False)
            subtask.parent_task = task
            subtask.save()
            form.save_m2m()
            return JsonResponse({'success': True})
        else:
            html = render_to_string('projects/partials/subtask_form.html', 
                                  {'form': form, 'task': task}, request=request)
            return JsonResponse({'success': False, 'form_html': html})
    else:
        form = SubTaskForm(parent_task=task)
        html = render_to_string('projects/partials/subtask_form.html', 
                              {'form': form, 'task': task}, request=request)
        return JsonResponse({'form_html': html})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def update_subtask_status(request, subtask_id):
    """Обновление статуса подзадачи через drag&drop"""
    try:
        subtask = get_object_or_404(SubTask, id=subtask_id)
        
        # Проверяем права
        if (request.user not in subtask.parent_task.assigned_to.all() and 
            request.user != subtask.parent_task.project.creator):
            return JsonResponse({'error': 'Нет прав на изменение подзадачи'}, status=403)
        
        data = json.loads(request.body)
        new_status_id = data.get('status_id')
        
        if not new_status_id:
            return JsonResponse({'error': 'Не указан статус'}, status=400)
        
        try:
            new_status = TaskStatus.objects.get(id=new_status_id)
        except TaskStatus.DoesNotExist:
            return JsonResponse({'error': 'Статус не найден'}, status=400)
        
        # Проверяем, что статус доступен для родительской задачи
        if new_status not in subtask.parent_task.get_available_statuses():
            return JsonResponse({'error': 'Статус недоступен для этой задачи'}, status=400)
        
        # Обновляем статус
        subtask.status = new_status
        
        # Автоматически обновляем даты
        if new_status.name == 'В работе' and not subtask.start_date:
            subtask.start_date = timezone.now().date()
        
        if new_status.name == 'Завершена' and not subtask.end_date:
            subtask.end_date = timezone.now().date()
        
        subtask.save()
        
        response_data = {
            'success': True,
            'subtask_id': subtask.id,
            'status_name': subtask.status.name,
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@login_required
def edit_subtask(request, subtask_id):
    """Редактирование подзадачи"""
    subtask = get_object_or_404(SubTask, id=subtask_id)
    
    # Проверяем права
    if (request.user not in subtask.parent_task.assigned_to.all() and 
        request.user != subtask.parent_task.project.creator and 
        request.user.role not in ['admin', 'director']):
        return JsonResponse({'success': False, 'error': 'Нет прав на редактирование подзадачи'})
    
    if request.method == 'POST':
        form = SubTaskForm(request.POST, instance=subtask, parent_task=subtask.parent_task)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            form_html = render_to_string('projects/partials/subtask_form.html', 
                                       {'form': form, 'task': subtask.parent_task}, 
                                       request=request)
            return JsonResponse({'success': False, 'form_html': form_html})
    else:
        form = SubTaskForm(instance=subtask, parent_task=subtask.parent_task)
        form_html = render_to_string('projects/partials/subtask_form.html', 
                                   {'form': form, 'task': subtask.parent_task}, 
                                   request=request)
        return JsonResponse({'form_html': form_html})