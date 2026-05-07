from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views
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
    path('workspaces/<int:workspace_id>/create_post/', views.create_post, name='create_post'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('workspaces/sub_workspaces/<int:workspace_id>', views.children_workspaces, name='children_workspaces'),
path('activate/<uidb64>/<token>/', views.activate_account, name='activate'),
    path('forgot-password/', auth_views.PasswordResetView.as_view(
        template_name='password_reset_form.html',
        html_email_template_name='password_reset_email.html',
subject_template_name='registration/password_reset_subject.txt',
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
