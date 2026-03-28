from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('api/chat/', views.chat_with_yana, name='chat_with_yana'),
    path('api/reset/', views.reset_conversation, name='reset_conversation'),
    path('api/analyze-journal/', views.analyze_journal_entry, name='analyze_journal_entry'),
    path('history/', views.yana_history, name='yana_history'),
    path('sessions/<int:session_id>/activate/', views.activate_session, name='activate_session'),
    path('api/sessions/<int:session_id>/title/', views.edit_session_title, name='edit_session_title'),
    path('api/sessions/<int:session_id>/delete/', views.delete_session, name='delete_session'),
]
