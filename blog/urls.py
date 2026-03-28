from django.urls import path

from . import views

urlpatterns = [
    path("", views.post_list, name="blog"),
    path("post/<slug:slug>/", views.post_detail, name="blog_post_detail"),
    path("post/<int:post_id>/bookmark/", views.toggle_bookmark, name="blog_bookmark_toggle"),
]
