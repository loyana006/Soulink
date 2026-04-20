from django.urls import path
from journal import views

urlpatterns = [
    path("", views.journal, name="journal"),
    path("auto-save/", views.auto_save_draft, name="journal_auto_save"),
    path("entries-more/", views.journal_entries_more, name="journal_entries_more"),
    path("entry/<int:id>/", views.view_journal_entry, name="view_journal_entry"),
    path("journal-entry/<int:id>/", views.get_journal_entry, name="get_journal_entry"),
    path(
        "journal-entry/<int:id>/delete/",
        views.delete_journal_entry,
        name="delete_journal_entry",
    ),
]
