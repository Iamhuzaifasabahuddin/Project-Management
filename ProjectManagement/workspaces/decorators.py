from django.core.exceptions import PermissionDenied
from functools import wraps
from .services import is_workspace_admin, is_workspace_member

def workspace_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # This assumes workspace_id or client_id is in kwargs, 
        # or it will need to be adapted based on the specific view
        if not request.user.is_superuser:
            # Simplistic check for now, might need context-aware retrieval
            if not is_workspace_admin(request.user, None): # Need workspace instance
                raise PermissionDenied("Workspace admin access required")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def workspace_member_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            # Need workspace instance
            if not is_workspace_member(request.user, None):
                raise PermissionDenied("Workspace member access required")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
