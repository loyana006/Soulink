from django.urls import path

from . import views


urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_user, name="logout"),
    path("profile/", views.profile_view, name="my_profile"),
    path(
        "profile/update-identity/",
        views.profile_update_identity,
        name="profile_update_identity",
    ),
    path(
        "profile/update-privacy/",
        views.profile_update_privacy,
        name="profile_update_privacy",
    ),
    path(
        "profile/safety-plan/",
        views.profile_safety_plan_save,
        name="profile_safety_plan_save",
    ),
    path(
        "profile/weekly-goal/",
        views.profile_weekly_goal,
        name="profile_weekly_goal",
    ),
    path("profile/export/", views.export_user_data, name="profile_export_data"),
    path("profile/password/", views.password_change_view, name="password_change"),
]
