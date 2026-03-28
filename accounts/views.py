from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import (
    LoginForm,
    UserSignUpForm,
)
from .backends import EmailOrUsernameBackend


def login_view(request):
    msg = None
    form = LoginForm(request.POST or None)

    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            backend = EmailOrUsernameBackend()
            user = backend.authenticate(
                request=request, username=username, password=password
            )

            if user is not None:
                login(request, user)

                if user.is_superuser:
                    return redirect("/admin/")

                return redirect("/")
            msg = "Invalid credentials"

        else:
            msg = "Invalid Inputs"

    return render(request, "auth/login.html", {"form": form, "msg": msg})


def signup_view(request):
    msg = None
    success = False

    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        form = UserSignUpForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("login")
        msg = "Form is not valid"
    else:
        form = UserSignUpForm()

    return render(
        request,
        "auth/signup.html",
        {"form": form, "msg": msg, "success": success},
    )


@login_required()
def logout_user(request):
    logout(request)
    return redirect("/")


@login_required()
def profile_view(request):
    return render(request, "profile.html")
