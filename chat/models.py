from django.db import models
from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model 
from PIL import Image
from io import BytesIO
import uuid
import os

def attachment_upload_path(instance, filename):
    return f"chat/{instance.message.room.id}/{uuid.uuid4()}_{filename}"

class ChatRoom(models.Model):
    TYPE_CHOICES = [
        ('direct', 'Личная переписка'),
        ('project', 'Проектный чат'),
    ]
    
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    project = models.ForeignKey('projects.Project', null=True, blank=True, on_delete=models.SET_NULL)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, 
                              on_delete=models.SET_NULL, 
                              null=True, 
                              blank=True,
                              related_name='created_chats')
    def get_last_message(self):
     return self.messages.order_by('-timestamp').first()

    def get_display_name(self):
        if self.type == 'direct':
            # Получаем участников чата, исключая текущего пользователя
            other_users = self.participants.exclude(id=self.creator.id if self.creator else None)
            other_user = other_users.first()
            return f"Чат с {other_user.get_full_name()}" if other_user else "Личный чат"
        elif self.type == 'project':
            return f"Проектный чат: {self.project.title if self.project else 'Общий'}"
        return "Чат"

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    edited = models.BooleanField(default=False)
    read = models.BooleanField(default=False)  # Добавьте это поле

    class Meta:
        ordering = ['timestamp']

class Attachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=attachment_upload_path)
    file_type = models.CharField(max_length=50, blank=True)
    thumbnail = models.ImageField(upload_to='chat/thumbs/', null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.file_type:
            self.file_type = self.guess_file_type()
        
        super().save(*args, **kwargs)
        
        if self.file_type.startswith('image/'):
            self.create_thumbnail()
    
    def guess_file_type(self):
        ext = os.path.splitext(self.file.name)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif']:
            return 'image' + ext
        return 'file' + ext
    
    def create_thumbnail(self):
        try:
            with default_storage.open(self.file.name) as f:
                image = Image.open(f)
                image.thumbnail((300, 300))
                
                thumb_io = BytesIO()
                image.save(thumb_io, format='JPEG')
                
                thumb_path = f"chat/thumbs/{uuid.uuid4()}.jpg"
                with default_storage.open(thumb_path, 'wb+') as thumb_file:
                    thumb_file.write(thumb_io.getvalue())
                
                self.thumbnail = thumb_path
                self.save(update_fields=['thumbnail'])
        except Exception as e:
            print(f"Error creating thumbnail: {e}")