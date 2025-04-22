# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import ChatRoom, Message, Attachment
from django.contrib.auth import get_user_model
from django.db.models import Max, Subquery, OuterRef, Exists
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.db import models
from django.utils import timezone

@login_required
def index(request):
    chats = ChatRoom.objects.filter(
        participants=request.user
    ).annotate(
        last_msg_time=Max('messages__timestamp'),
        last_message_content=Subquery(
            Message.objects.filter(room=OuterRef('pk'))
            .order_by('-timestamp')
            .values('content')[:1]
        ),
        last_message_sender=Subquery(
            Message.objects.filter(room=OuterRef('pk'))
            .order_by('-timestamp')
            .values('sender__username')[:1]
        ),
        unread_count=models.Count(
            'messages',
            filter=models.Q(messages__read=False) & 
            ~models.Q(messages__sender=request.user)
        )
    ).order_by('-last_msg_time').prefetch_related('participants')
    
    User = get_user_model()
    users = User.objects.exclude(id=request.user.id)  # Исключаем текущего пользователя
    return render(request, 'chat/index.html', {
        'chats': chats,
        'users': users,
        'current_user': request.user
    })

@login_required
@require_POST
def create_direct_chat(request):
    user_id = request.POST.get('user_id')
    User = get_user_model()
    
    try:
        other_user = User.objects.get(id=user_id)
        existing_chat = ChatRoom.objects.filter(
            type='direct',
            participants=request.user
        ).filter(participants=other_user).first()
        
        if existing_chat:
            return JsonResponse({
                'success': True,
                'chat_id': existing_chat.id
            })
        
        new_chat = ChatRoom.objects.create(type='direct', creator=request.user)
        new_chat.participants.add(request.user, other_user)
        
        return JsonResponse({
            'success': True,
            'chat_id': new_chat.id
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=400)

@login_required
def chat_messages(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if request.user not in room.participants.all():
        return HttpResponseForbidden()
    
    messages = room.messages.order_by('timestamp').annotate(
        has_attachment=Exists(Attachment.objects.filter(message=OuterRef('pk')))
    )
    
    if not messages.exists():
        return JsonResponse([], safe=False)
    
    messages = messages.values(
        'id',
        'content',
        'timestamp',
        'has_attachment',
        'sender__username',
        is_my=models.ExpressionWrapper(
            models.Q(sender=request.user),
            output_field=models.BooleanField()
        ),
        attachment_url=Subquery(
            Attachment.objects.filter(message=OuterRef('pk'))
            .values('file')[:1]
        ),
        attachment_name=Subquery(
            Attachment.objects.filter(message=OuterRef('pk'))
            .values('file')[:1]
        )
    )
    
    room.messages.exclude(sender=request.user).update(read=True)
    
    return JsonResponse(list(messages), safe=False) 

@login_required
@require_POST
def send_message(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if request.user not in room.participants.all():
        return HttpResponseForbidden()
    
    content = request.POST.get('content', '').strip()
    file = request.FILES.get('file')
    
    if not content and not file:
        return HttpResponseBadRequest("Message content or file is required")
    
    message = Message.objects.create(
        room=room,
        sender=request.user,
        content=content
    )
    
    attachment = None
    if file:
        attachment = Attachment.objects.create(
            message=message,
            file=file
        )
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'sender': request.user.username,
            'file_url': attachment.file.url if attachment else None,
            'file_name': attachment.file.name if attachment else None
        }
    })

@login_required
def search_chats(request):
    query = request.GET.get('q', '')
    chats = ChatRoom.objects.filter(
        participants=request.user
    ).annotate(
        display_name=models.Case(
            models.When(type='direct', then=models.Subquery(
                get_user_model().objects.filter(
                    chat_rooms=OuterRef('pk')
                ).exclude(id=request.user.id)
                .values('username')[:1]
            )),
            models.When(type='project', then=models.F('project__title')),
            default=models.Value('Чат'),
            output_field=models.CharField()
        )
    ).filter(
        models.Q(participants__username__icontains=query) |
        models.Q(project__title__icontains=query) if query else models.Q()
    ).annotate(
        last_msg_time=Max('messages__timestamp'),
        last_message_content=Subquery(
            Message.objects.filter(room=OuterRef('pk'))
            .order_by('-timestamp')
            .values('content')[:1]
        ),
        unread_count=models.Count(
            'messages',
            filter=models.Q(messages__read=False) & 
            ~models.Q(messages__sender=request.user)
        )
    ).values(
        'id',
        'display_name',
        'last_msg_time',
        'last_message_content',
        'unread_count'
    )
    
    return JsonResponse(list(chats), safe=False)
    
    return JsonResponse(list(chats), safe=False)
def room_view(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if request.user not in room.participants.all():
        return HttpResponseForbidden()

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                room=room,
                sender=request.user,
                content=content
            )
            return redirect('chat:room', room_id=room.id)