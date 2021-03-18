from typing import ContextManager
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.deletion import CASCADE
from django.db.models.fields import AutoField
from django.utils.timezone import now
# Create your models here.
adminUser=get_user_model()
def upload_image(instance, filename):
    return "%s/%s" % (instance.question_id, filename)


class User(models.Model):
    id=models.AutoField(primary_key=True)
    username=models.CharField(max_length=200,unique=True)
    firstName=models.CharField(max_length=50)
    lastName=models.CharField(max_length=50)
    password=models.CharField(max_length=50)
    image=models.ImageField(upload_to='profile_image/',null=True, blank=True, default='userdefault.png')
    about=models.CharField(max_length=1200,blank=True)
    phonenumber=models.CharField(max_length=12)
    email=models.EmailField(unique=True)

class Room(models.Model):
    id=models.AutoField(primary_key=True)
    name=models.CharField(max_length=200)
    members=models.ManyToManyField(User, related_name='member')
    admins=models.ManyToManyField(User,related_name='admin')
    image=models.ImageField(upload_to='room_icon/',null=True, blank=True, default='roomdefault.jpg')
    description=models.TextField(null=True)

class Message(models.Model):
    author=models.ForeignKey(User, related_name='author_messages',on_delete=models.CASCADE)
    content=models.TextField(blank=True)
    timestamp=models.DateTimeField(auto_now=True)
    room=models.ForeignKey(Room,on_delete=models.CASCADE,related_name='message_room')
    image=models.ImageField(upload_to='room_images/',null=True, blank=True)
    def __str__(self):
        return self.author.username

    def last_10_messages(self):
        return Message.objects.order_by('-timestamp').all()[:10]