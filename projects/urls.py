from django.urls import path
from . import views  # Убедись, что импортируется views из текущего приложения
from .views import project_detail, task_detail, start_task, complete_task,revert_to_pending,revert_to_in_progress
urlpatterns = [
    path('', views.project_list, name='project_list'),  
    path('<int:project_id>/', views.project_detail, name='project_detail'),
    path('create/', views.create_project, name='create_project'),
    path('<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('<int:project_id>/tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:task_id>/update_status/', views.update_task_status, name='update_task_status'),
    path('tasks/<int:task_id>/', task_detail, name='task_detail'),
    path('tasks/<int:task_id>/start/', start_task, name='start_task'),
    path('tasks/<int:task_id>/complete/', complete_task, name='complete_task'),
    path('tasks/<int:task_id>/revert_to_pending/', revert_to_pending, name='revert_to_pending'),
    path('tasks/<int:task_id>/revert_to_in_progress/', revert_to_in_progress, name='revert_to_in_progress'),
    path('tasks/<int:task_id>/update_status/', views.update_task_status_ajax, name='update_task_status_ajax'),
    path('employees/', views.employee_list, name='employee_list'),
    path('task/<int:task_id>/edit/', views.edit_task, name='edit_task'),
   path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
   path('projects/<int:project_id>/create_task_modal/', views.create_task_modal, name='create_task_modal'),
]
