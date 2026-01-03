from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class LoginForm(forms.Form):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter Your Email or Username",
                "id": "loginEmail",
                "class": "form-control form-control-custom",
            }
        ),
    )

    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter Your Password",
                "id": "loginPassword",
                "class": "form-control form-control-custom",
            }

        ),
    )


class UserSignUpForm(UserCreationForm):
    # first_name = forms.CharField(
    #     required=True,
    #     widget=forms.TextInput(),
    # )
    # last_name = forms.CharField(
    #     required=True,
    #     widget=forms.TextInput(),
    # )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter Your Email",
                "id": "loginEmail",
                "class": "form-control form-control-custom",
            }
        ),
    )
    # phone_number = forms.CharField(
    #     required=True,
    #     widget=forms.TextInput(),
    # )
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter Your Username",
                "id": "loginEmail",
                "class": "form-control form-control-custom",
            }
        ),
    )
    # address = forms.CharField(
    #     required=False,
    #     widget=forms.TextInput(),
    # )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter Your Password",
                "id": "loginEmail",
                "class": "form-control form-control-custom",
            }
        ),
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter Your Password Again",
                "id": "loginEmail",
                "class": "form-control form-control-custom",
            }
        ),
    )

    class Meta:
        model = CustomUser
        fields = (
            # "first_name",
            # "last_name",
            # "address",
            "username",
            "email",
            # "phone_number",
            "password1",
            "password2",
        )
