# accounts/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import RegisterForm, WorkspaceForm, RoleAssignForm
from .models import Workspace, Membership


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']

            login(request, user)
            return redirect('dashboard')

        return render(request, 'accounts/register.html', {'form': form})
    return None


def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            print("User logged in")
            return redirect('dashboard')
        else:
            error = "Invalid username or password."
    return render(request, 'accounts/login.html', {'error': error})

@login_required
def dashboard_view(request):
    workspaces = Workspace.objects.filter(membership__user=request.user)
    return render(request, 'accounts/dashboard.html', {'workspaces': workspaces})


def logout_view(request):
    logout(request)
    return redirect('login')



@login_required
def create_workspace(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Only superuser can create workspaces")

    form = WorkspaceForm(request.POST or None)

    if form.is_valid():
        workspace = form.save(commit=False)
        workspace.owner = request.user
        workspace.save()
        return redirect('workspace_list')

    return render(request, 'accounts/create_workspace.html', {'form': form})



@login_required
def assign_role(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Only superuser can assign roles")

    form = RoleAssignForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('workspace_list')

    return render(request, 'accounts/assign_role.html', {'form': form})



@login_required
def workspace_list(request):
    if not request.user.is_superuser:
        workspaces = Workspace.objects.all()

        memberships = Membership.objects.select_related('user', 'workspace')

        return render(request, 'accounts/workspace_list.html', {
            'workspaces': workspaces,
            'memberships': memberships
        })
    return None


def custom_403_view(request, exception):
    return render(request, '403.html', status=403)