from django.urls import path
from . import views

urlpatterns = [
    path("", views.confessions, name="confessionals"),
    path("feed/more/", views.confession_feed_more, name="confession_feed_more"),
    path("<int:confession_id>/delete/", views.delete_confession, name="delete_confession"),
    path("<int:confession_id>/publish/", views.publish_confession, name="publish_confession"),
    path(
        "<int:confession_id>/anonymous/",
        views.toggle_confession_anonymous,
        name="toggle_confession_anonymous",
    ),
    path("<int:confession_id>/like/", views.toggle_like, name="toggle_confession_like"),
    path("<int:confession_id>/comment/", views.add_comment, name="add_confession_comment"),
]
