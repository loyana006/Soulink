from django.urls import path
from . import views

urlpatterns = [
    path("", views.confessions, name="confessionals"),
    path("<int:confession_id>/like/", views.toggle_like, name="toggle_confession_like"),
    path("<int:confession_id>/comment/", views.add_comment, name="add_confession_comment"),
]
