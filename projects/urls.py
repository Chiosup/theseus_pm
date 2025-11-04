from django.urls import path
from . import views

urlpatterns = [
    # Проекты
    path('', views.project_list, name='project_list'),
    path('create/', views.create_project, name='create_project'),
    path('<int:project_id>/', views.project_detail, name='project_detail'),
    path('<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('<int:project_id>/duplicate/', views.duplicate_project, name='duplicate_project'),
    
    # Задачи внутри проектов
    path('<int:project_id>/create_task/', views.create_task_modal, name='create_task_modal'),
    
    # Отдельные задачи (без привязки к проекту в URL)
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('task/<int:task_id>/start/', views.start_task, name='start_task'),
    path('task/<int:task_id>/complete/', views.complete_task, name='complete_task'),
    path('task/<int:task_id>/reopen/', views.reopen_task, name='reopen_task'),
    path('task/<int:task_id>/revert_to_pending/', views.revert_to_pending, name='revert_to_pending'),
    path('task/<int:task_id>/revert_to_in_progress/', views.revert_to_in_progress, name='revert_to_in_progress'),
    path('task/<int:task_id>/update_status/', views.update_task_status, name='update_task_status'),
    
    # Сотрудники
    path('employees/', views.employee_list, name='employee_list'),
]