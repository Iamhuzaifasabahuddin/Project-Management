from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [

    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('workspaces/', views.workspace_list, name='workspace_list'),
    path('workspaces/create/', views.create_workspace, name='create_workspace'),
    path('roles/assign/', views.assign_role, name='assign_role'),
    path('workspaces/<int:workspace_id>/', views.workspace_detail, name='workspace_detail'),
    path('clients/<int:workspace_id>/', views.client_detail, name='client_details'),
    path('clients/<int:client_id>/posts', views.client_posts, name='client_posts'),
    path('workspaces/<int:client_id>/create_post/', views.create_post, name='create_post'),
    # path('workspaces/<int:workspace_id>/<int:post_id>/delete_post/', views.delete_post, name='delete_post'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('workspaces/clients/<int:workspace_id>', views.client_list, name='client_list'),
    path('workspaces/add_client/<int:workspace_id>', views.create_clients, name='create_client'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate'),
    path('forgot-password/', auth_views.PasswordResetView.as_view(
        template_name='password_reset_form.html',
        html_email_template_name='password_reset_email.html',
        subject_template_name='password_reset_subject.txt',
    ), name='password_reset'),

    path('forgot-password/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html',

    ), name='password_reset_complete'),
]
