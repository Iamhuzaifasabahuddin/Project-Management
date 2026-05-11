from django.contrib.auth import views as auth_views
from django.urls import path

from  . import views

urlpatterns = [

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
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
