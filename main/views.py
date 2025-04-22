from django.shortcuts import render
from projects.models import Project, Task

def index(request):
    search_query = request.GET.get('q', '')

    projects = Project.objects.all()
    tasks = Task.objects.all()

    if search_query:
        projects = projects.filter(title__icontains=search_query)
        tasks = tasks.filter(title__icontains=search_query)

    context = {
        'projects': projects,
        'tasks': tasks,
        'search_query': search_query
    }
    return render(request, 'main/index.html', context)
