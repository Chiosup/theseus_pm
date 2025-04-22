from django.urls import path
from . import views

app_name = 'chat'
urlpatterns = [
   
    path('', views.index, name='index'),
    path('create-direct/', views.create_direct_chat, name='create_direct'),  
    path('room/<int:room_id>/', views.room_view, name='room'),
    path('search/', views.search_chats, name='chat_search'),
    path('<int:room_id>/messages/', views.chat_messages, name='chat_messages'),
    path('<int:room_id>/send/', views.send_message, name='send_message'),
]