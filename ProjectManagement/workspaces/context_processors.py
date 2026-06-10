from workspaces.models import Membership

def admin_check(request):
    if not request.user.is_authenticated:
        return {'is_system_admin': False}
    
    is_admin = request.user.is_superuser or Membership.objects.filter(
        user=request.user,
        role__iexact="admin"
    ).exists()
    
    return {'is_system_admin': is_admin}
