from os import name, urandom
from django.contrib import admin
from django.core.checks import messages
from django.db import reset_queries
from django.db.models import query
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from .models import Message, Room, User
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import random
import string
from django.conf import settings 
from django.core.mail import send_mail
# Create your views here.
def rand_pass(size=6):  
    generate_pass = ''.join([random.choice( string.ascii_uppercase +
                                            string.ascii_lowercase +
                                            string.digits)  
                                            for n in range(size)])
    return generate_pass

def rooms_to_json(rooms_objects):
    rooms = []
    for room in rooms_objects:
        rooms.append(room_to_json(room))
    return rooms


def room_to_json(room):
    return {
        'id': room.id,
        'name': room.name,
        'image': room.image.url,
    }


def users_to_json(user_objects, admins):
    users = []
    for user in user_objects:
        users.append(user_to_json(user, admins))
    return users


def user_to_json(user, admins):
    if user in admins:
        return {
            'username': user.username,
            'name': user.firstName,
            'image': user.image.url,
            'admin': "1"
        }
    else:
        return {
            'username': user.username,
            'name': user.firstName,
            'image': user.image.url,
            'admin': "0"
        }
def index(request):
    return render(request, 'chat/index.html')
def login(request):
        if request.method=='POST':
            userName = request.POST.get('username')
            password = request.POST.get('password')
        user = User.objects.filter(username=userName, password=password)
        if user:
            request.session['username'] = userName
            return JsonResponse({'login':'1','message':""})
        else:
            return JsonResponse({'login':'0','message':"No such user exists"})
    
def home(request):
    if request.session.has_key('username'):
        username = request.session['username']
        user = User.objects.filter(username=username)[0]
        rooms = user.member.all()
        return render(request, 'chat/home.html', {'instance': user, 'joined_rooms': rooms, 'not_joined_rooms': []})
    else:
        return redirect('/index')


def signup(request):
    if request.method=='POST':
        email=request.POST.get('email')
        firstName = request.POST.get('first_name')
        lastName = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        a=User.objects.filter(email=email)
        b=User.objects.filter(username=username)
        if a or b:
            return JsonResponse({'created':'0','message':"User already exists"})
        User.objects.create(firstName=firstName, lastName=lastName,username=username, password=password,email=email)
        return JsonResponse({'created':'1','message':"Signup Successful, Login to continue"})
    else:
        return render(request, 'chat/signup.html')






def create_room(request):
    if request.session.has_key('username'):
        username = request.session['username']
        user = User.objects.filter(username=username)[0]
        name = request.POST.get('name').lower()
        rooms=Room.objects.filter(name=name)
        if rooms:
            return JsonResponse({'created':'0','message':"Room already exists"})
        image = request.FILES.get('image')
        if image is not None:
            room = Room.objects.create(name=name, image=image)
        else:
            room = Room.objects.create(name=name)
        room.save()
        room.members.add(user)
        room.admins.add(user)
        room.save()
        return JsonResponse({'created':'1','message':"Room created successfully"})
    else:
        return redirect('/index')


def room(request, room_name):
    if request.session.has_key('username'):
        room = Room.objects.filter(name=room_name)[0]
        if request.method=="POST":
            image = request.FILES.get('image')
            
            imagemsg=Message.objects.create(author= get_object_or_404(User, username=request.session['username']),image=image,room=room)
            channel_layer = get_channel_layer()
            message={'author':imagemsg.author.username,'content':imagemsg.content,'image':imagemsg.image.url,'timestamp':str(imagemsg.timestamp),'room':imagemsg.room.name}
            roomgrp="chat_"+room.name
            async_to_sync(channel_layer.group_send)(
                roomgrp,
                    {
                     'type': 'image_message',
                     'message':message
                    }
                )
            return HttpResponse("Success")
        else:
            messages = Message.objects.filter(room=room)
            return render(request, 'chat/room.html', {
                'user': get_object_or_404(User, username=request.session['username']),
                'instance': room,
                'room_name_json': mark_safe(json.dumps(room_name)),
                'username': mark_safe(json.dumps(request.session['username'])),
                'messages': messages,
            })
    else:
        return redirect('/index')


def joinRoom(request, room_name):
    if request.session.has_key('username'):
        username = request.session['username']
        user = get_object_or_404(User, username=username)
        room = get_object_or_404(Room, name=room_name)
        room.members.add(user)
        room.save()
        return redirect('/home')
    else:
        return redirect('/index')


@csrf_exempt
def search_room(request):
    username = request.session['username']
    query = request.POST.get('query')
    rooms = Room.objects.filter(name__contains=query)
    rooms = rooms.exclude(members__username=username)
    rooms = rooms_to_json(rooms)
    return JsonResponse(rooms, safe=False)


def roomInfo(request, room_name):
    if request.session.has_key('username'):
        username = request.session['username']
        user = get_object_or_404(User, username=username)
        room = get_object_or_404(Room, name=room_name)
        room_members = room.members.all()
        room_members_json = users_to_json(room_members, room.admins.all())
        room_admins = room.admins.all()
        if user in room_admins:
            editable = "1"
        else:
            editable = "0"
        return render(request, 'chat/room_info.html', {'room_members': room_members_json, 'instance': user, 'room': room, 'editable': editable})
    else:
        return redirect('/index')


def userInfo(request, user_name):
    if request.session.has_key('username'):
        username = request.session['username']
        user = get_object_or_404(User, username=username)
        user_info = get_object_or_404(User, username=user_name)
        rooms1 = user.member.all()
        rooms2 = user_info.member.all()
        common_rooms = rooms1.intersection(rooms2)
        return render(request, 'chat/user_info.html', {'instance': user, 'user_info': user_info, 'rooms': common_rooms})
    else:
        return redirect('/index')


def editRoom(request, room_name):
    if request.session.has_key('username'):
        user = get_object_or_404(User, username=request.session['username'])
        room = get_object_or_404(Room, name=room_name)
        admins = room.admins.all()
        if user in admins:
            return render(request, 'chat/edit_room.html', {'room': room, 'instance': user, 'editable': "1"})
        else:
            return render(request, 'chat/edit_room.html', {'room': room, 'instance': user, 'editable': "0"})
    else:
        return redirect('/index')


def saveRoom(request):
    if request.session.has_key('username'):
        username = request.session['username']
        user = get_object_or_404(User, username=username)
        name = request.POST.get('name')
        desc = request.POST.get('description')
        image = request.FILES.get('image')
        room = get_object_or_404(Room, name=name)
        if image is not None:
            room.image = image
            room.description = desc
            room.save()
        else:
            room.description = desc
            room.save()
        return redirect('/room/'+room.name)
    else:
        return redirect('/index')



def addAdmin(request):
    if request.session.has_key('username'):
        username = request.session['username']
        user = get_object_or_404(User, username=username)
        room=get_object_or_404(Room,name=request.GET.get('room'))
        room_admins = room.admins.all()
        if user in room_admins:
            userTobeAdmin=get_object_or_404(User,username=request.GET.get('user'))
            room.admins.add(userTobeAdmin)
            room.save()
            return redirect('/room/'+room.name)
        else:
            return redirect('/room/'+room.name)
    else:
        return redirect('/index')

def removeAdmin(request):
    if request.session.has_key('username'):
        username = request.session['username']
        user = get_object_or_404(User, username=username)
        room=get_object_or_404(Room,name=request.GET.get('room'))
        room_admins = room.admins.all()
        if user in room_admins:
            userTobeAdmin=get_object_or_404(User,username=request.GET.get('user'))
            room.admins.remove(userTobeAdmin)
            room.save()
            return redirect('/room/'+room.name)
        else:
            return redirect('/room/'+room.name)
    else:
        return redirect('/index')
    

def allRooms(request):
    if request.session.has_key('username'):
        user=get_object_or_404(User,username=request.session['username'])
        rooms=Room.objects.all()
        return render(request,'chat/allRooms.html',{'instance':user,'rooms':rooms})
    else:
        return redirect('/index')

def removeMember(request):
    if request.session.has_key('username'):
        username = request.session['username']
        user = get_object_or_404(User, username=username)
        room=get_object_or_404(Room,name=request.GET.get('room'))
        room_admins = room.admins.all()
        if user in room_admins:
            userTobeAdmin=get_object_or_404(User,username=request.GET.get('user'))
            room.members.remove(userTobeAdmin)
            room.save()
            return redirect('/room/'+room.name)
        else:
            return redirect('/room/'+room.name)
    else:
        return redirect('/index')

def profile(request):
    if request.session.has_key('username'):
        user=get_object_or_404(User,username=request.session['username'])
        return render(request,'chat/profile.html',{'instance':user})
    else:
        return redirect('/index')

def updateProfileImage(request):
    if request.session.has_key('username'):
        user=get_object_or_404(User,username=request.session['username'])
        image=request.FILES.get('image')
        user.image=image
        user.save()
        return JsonResponse({'image':user.image.url})
    else:
        return redirect('/index')

def updatePassword(request):
    if request.session.has_key('username'):
        user=get_object_or_404(User,username=request.session['username'])
        oldpass=request.POST.get('old_pass')
        newpass=request.POST.get('new_pass')
        if user.password==oldpass:
            user.password=newpass
            user.save()
            return JsonResponse({'updated':'1','message':'Password Updated successfully'})
        else:
            return JsonResponse({'updated':'0','message':'Old Password dosent match'})
    else:
        return redirect('/index')

def updateInfo(request):
    if request.session.has_key('username'):
        user=get_object_or_404(User,username=request.session['username'])
        firstName=request.POST.get('first_name')
        lastName=request.POST.get('last_name')
        about=request.POST.get('about')
        phone=request.POST.get('phone')
        user.lastName=lastName
        user.firstName=firstName
        user.about=about
        user.phonenumber=phone
        user.save()
        return JsonResponse({'firstName':firstName,'lastName':lastName,'phone':phone,'about':about})
    else:
        return redirect('/index')

def logout(request):
    if request.session.has_key('username'):
        request.session.pop('username')
        return redirect('/index')
    else:
        return redirect('/index')

def forget_pass(request):
    if request.method == 'POST':
            ur = request.POST.get('username')
            dbuser = User.objects.filter(username=ur)
            if not dbuser:
                return JsonResponse({'updated':"0",'message':"No such User Exists"})
            else:
                dbuser=dbuser[0]
                ran_pass=rand_pass()
                subject = 'Reset Password'
                message = "Hi {}, thank you for contacting Connect-e-Fans.\nYour temporary password is {}.\n Go to profile section to update your password.".format(dbuser.firstName,ran_pass)
                email_from = settings.EMAIL_HOST_USER 
                recipient_list = [dbuser.email, ]
                send_mail( subject, message, email_from, recipient_list )
                user = get_object_or_404(User, username=ur)
                user.password=ran_pass
                user.save()
                return JsonResponse({'updated':"1",'message':"Email sent Successfully"})
    else:
        return redirect('/forgetpassword')

def forgetPassword(request):
    return render(request, 'chat/forgetpass.html')