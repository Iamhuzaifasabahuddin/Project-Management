# Test comment
from django.urls import path
from . import views

urlpatterns = [
    path('tasks/all/', views.all_user_tasks, name='all_user_tasks'),
    path('teams/<int:task_id>/create_post/', views.create_post, name='create_post'),
    path('teams/<int:team_id>/create_task/', views.create_task, name='create_task'),
    path('teams/<int:team_id>/tasks/', views.team_tasks, name='team_tasks'),
    path('task/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    # path('task/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('posts/<int:post_id>/delete/', views.delete_post, name='delete_task_post'),
    path('task/<int:task_id>/posts/', views.task_posts, name='task_posts'),
    path('task/<int:task_id>/complete/request', views.task_completion_request, name='task_completion_request'),
    path('task/<int:task_id>/approve/', views.task_approve, name='task_approve'),
    path('task/<int:task_id>/decline/', views.task_decline, name='task_decline'),
]