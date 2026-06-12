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
    path('teams/all/', views.all_user_teams, name='all_user_teams'),
    path('clients/<int:client_id>/teams/', views.client_teams, name='client_teams'),
    # =========================
    # TEAM MANAGEMENT
    # =========================
    path('team/client/<int:client_id>/create/', views.create_team, name='create_team'),
    path('team/<int:team_id>/manage-members/', views.manage_team_members, name='manage_team_members'),
    path('team/<int:team_id>/delete/', views.delete_team, name='delete_team'),
]
