from django.shortcuts import render
from projects.models import Project, Task, TaskStatus
from django.db.models import Count

def index(request):
    search_query = request.GET.get('q', '')

    # Подбираем проекты в зависимости от прав пользователя (как в projects.project_list)
    if request.user.is_authenticated:
        if request.user.is_superuser:
            projects = Project.objects.all()
        elif request.user.groups.filter(name="Менеджеры").exists():
            projects = Project.objects.filter(creator=request.user)
        else:
            projects = Project.objects.filter(participants=request.user)
    else:
        # Для неаутентифицированных — пустой список
        projects = Project.objects.none()

    tasks = Task.objects.filter(project__in=projects)

    if search_query:
        projects = projects.filter(title__icontains=search_query)
        tasks = tasks.filter(title__icontains=search_query)

    # Рассчитываем статистику для диаграмм
    total_projects = projects.count()

    # Статистика по стадиям проекта (группируем по Project.stage)
    project_status_data = []
    stage_counts = projects.values('stage__id', 'stage__name', 'stage__color')\
                          .annotate(count=Count('id'))\
                          .order_by('-count')

    for sc in stage_counts:
        name = sc.get('stage__name') or 'Без стадии'
        color = sc.get('stage__color') or '#6c757d'
        project_status_data.append({
            'name': name,
            'count': sc.get('count', 0),
            'color': color,
        })

    # Общая статистика по задачам
    total_tasks = 0
    completed_tasks = 0

    for project in projects:
        project_tasks = project.tasks.all()
        total_project_tasks = project_tasks.count()
        total_tasks += total_project_tasks

        project_completed_tasks = project_tasks.filter(
            status__is_final=True
        ).count()
        completed_tasks += project_completed_tasks

        # Сохраняем вычисленный процент в объекте проекта для шаблона
        project.calculated_completion = 0
        if total_project_tasks > 0:
            project.calculated_completion = round((project_completed_tasks / total_project_tasks) * 100)

    overall_completion = 0
    if total_tasks > 0:
        overall_completion = round((completed_tasks / total_tasks) * 100)

    context = {
        'projects': projects,
        'tasks': tasks,
        'search_query': search_query,
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overall_completion': overall_completion,
        'project_status_data': project_status_data,
    }
    return render(request, 'main/index.html', context)
