from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('api/chat/', views.chat_with_yana, name='chat_with_yana'),
    path('api/reset/', views.reset_conversation, name='reset_conversation'),
    path('api/analyze-journal/', views.analyze_journal_entry, name='analyze_journal_entry'),
]
