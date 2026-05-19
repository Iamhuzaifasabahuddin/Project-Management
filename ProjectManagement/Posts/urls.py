from django.urls import path
from . import views

urlpatterns = [
    path('workspaces/<int:client_id>/create_post/', views.create_post, name='create_post'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('posts/<int:post_id>/delete', views.delete_post, name='delete_post'),
]