
from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin-hub/', views.admin_hub, name='admin_hub'),
    path('', views.dashboard_view, name='landing'),
    path('workspaces/', views.workspace_list, name='workspace_list'),
    path('workspaces/create/', views.create_workspace, name='create_workspace'),
    path('roles/assign/', views.assign_role, name='assign_role'),
    path('workspaces/<int:workspace_id>/', views.workspace_detail, name='workspace_detail'),
    path('workspace/<int:workspace_id>/clients', views.client_detail, name='client_details'),
    path('workspace/<int:workspace_id>/clients/list', views.client_list, name='client_list'),
    path('client/<int:client_id>', views.view_client_details, name='view_client'),
    path('client/<int:client_id>/edit', views.edit_client, name='edit_client'),
    path('workspaces/<int:workspace_id>/add client', views.create_clients, name='create_client'),
    path('allclients/', views.all_clients, name='all_clients'),
    path('clients/export-archived/', views.export_archived_clients, name='export_archived_clients'),
]