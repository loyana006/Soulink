from django.urls import path
from journal import views

urlpatterns = [
    path("", views.journal, name="journal"),
    path("journal-entry/<int:id>/", views.get_journal_entry, name="get_journal_entry"),
    path(
        "journal-entry/<int:id>/delete/",
        views.delete_journal_entry,
        name="delete_journal_entry",
    ),
]
