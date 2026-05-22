"""
URL Configuration for Team Management Views

Add these patterns to your Django URLs.
"""

from django.urls import path
from . import views

urlpatterns = [
    # =========================
    # TEAM LISTS & DASHBOARD
    # =========================
    path('clients/<int:client_id>/teams/', views.client_teams, name='client_teams'),
    path('teams/client/<int:client_id>/list/', views.team_list, name='team_list'),

    # =========================
    # TEAM CONTENT
    # =========================
    path('teams/<int:team_id>/posts/', views.team_posts, name='team_posts'),
    path('team/<int:team_id>/details/', views.team_detail, name='team_detail'),
    path('team/<int:team_id>/statistics/', views.team_statistics, name='team_statistics'),

    # =========================
    # TEAM MANAGEMENT
    # =========================
    path('team/client/<int:client_id>/create/', views.create_team, name='create_team'),
    path('team/<int:team_id>/manage-members/', views.manage_team_members, name='manage_team_members'),
    path('team/<int:team_id>/add-member/<int:user_id>/', views.add_user_to_team, name='add_user_to_team'),
    path('team/<int:team_id>/remove-member/<int:user_id>/', views.remove_user_from_team, name='remove_user_from_team'),
    path('team/<int:team_id>/delete/', views.delete_team, name='delete_team'),
]
