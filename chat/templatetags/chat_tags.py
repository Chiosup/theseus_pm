# chat/templatetags/chat_tags.py
from django import template
from chat.models import ChatRoom
from django.db.models import Max
register = template.Library()

@register.simple_tag
def get_user_chats(user):
    """Возвращает чаты пользователя с аннотацией времени последнего сообщения"""
    return ChatRoom.objects.filter(
        participants=user
    ).annotate(
        last_msg_time=Max('messages__timestamp')  # Теперь Max доступен
    ).order_by('-last_msg_time')[:5]  # Сортируем по времени последнего сообщения