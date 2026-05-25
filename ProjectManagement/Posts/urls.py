from django.urls import path
from . import views

urlpatterns = [
    path('teams/<int:task_id>/create_post/', views.create_post, name='create_post'),
    path('teams/<int:team_id>/create_task/', views.create_task, name='create_task'),
    path('teams/<int:team_id>/tasks/', views.team_tasks, name='team_tasks'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
]