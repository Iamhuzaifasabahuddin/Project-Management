# =========================
# IMPORTS
# =========================

from allauth.account.forms import default_token_generator
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from .forms import (
    RegisterForm,

)


from .tasks import send_verification_email_task

# =========================
# AJAX VALIDATION
# =========================

def check_username(request):
    username = request.GET.get('username', None)
    data = {
        'usernameExists': User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(data)


def check_email(request):
    email_part = request.GET.get('email', None)
    data = {
        'emailExists': User.objects.filter(email__iexact=email_part).exists()
    }
    return JsonResponse(data)

def check_reset_email(request):
    email = request.GET.get('resetEmail', None)
    data = {
        'emailExists': User.objects.filter(email__iexact=email).exists()
    }
    return JsonResponse(data)

# =========================
# AUTH FLOW
# =========================

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            activation_link = request.build_absolute_uri(
                f"/activate/{uid}/{token}/"
            )

            send_verification_email_task.delay(
                user_id=user.id,
                subject="Verify your account",
                template="emails/verify_account.html",
                context={
                    "name": user.first_name,
                    "activation_link": activation_link,
                },
            )

            messages.success(
                request,
                "Account created! Please verify your email.",
            )
            return redirect("login")

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Account activated successfully.")
        return redirect("login")

    return render(request, "accounts/activation_failed.html")


def login_view(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = User.objects.filter(
            Q(username=username) | Q(email=username)
        ).first()

        if not user or not user.check_password(password):
            error = "Invalid credentials."
        elif not user.is_active:
            error = "Please verify your email."
        else:
            login(request, user)
            return redirect("dashboard")

    return render(request, "accounts/login.html", {"error": error})


def logout_view(request):
    messages.success(request, "Logged out successfully.")
    logout(request)
    return redirect("login")


# =========================
# ERROR HANDLERS
# =========================

def custom_404_view(request, exception):
    return render(request, "404.html", status=404)


def custom_403_view(request, exception):
    return render(request, "403.html", status=403)


def custom_500_view(request):
    return render(request, "500.html", status=500)


def custom_401_view(request):
    return render(request, "401.html", status=401)
