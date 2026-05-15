# contacts/views/auth.py
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render


def admin_login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    error = None
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            error = "Invalid username or password."
    return render(request, "contacts/login.html", {"error": error})


def admin_logout_view(request):
    logout(request)
    return redirect("landing")
