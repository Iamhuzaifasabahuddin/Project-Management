
from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.dashboard_view, name='dashboard'),
    path('workspaces/', views.workspace_list, name='workspace_list'),
    path('workspaces/create/', views.create_workspace, name='create_workspace'),
    path('roles/assign/', views.assign_role, name='assign_role'),
    path('workspaces/<int:workspace_id>/', views.workspace_detail, name='workspace_detail'),
    path('clients/<int:workspace_id>/', views.client_detail, name='client_details'),
    path('clients/<int:client_id>/posts', views.client_posts, name='client_posts'),
    path('workspaces/clients/<int:workspace_id>', views.client_list, name='client_list'),
    path('workspaces/add_client/<int:workspace_id>', views.create_clients, name='create_client'),
]