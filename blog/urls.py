from django.urls import path

from . import views

urlpatterns = [
    path("", views.post_list, name="blog"),
    path("write/", views.write_post, name="blog_write"),
    path("saved/", views.saved_posts, name="blog_saved_posts"),
    path("post/<slug:slug>/", views.post_detail, name="blog_post_detail"),
    path("post/<int:post_id>/bookmark/", views.toggle_bookmark, name="blog_bookmark_toggle"),
]
