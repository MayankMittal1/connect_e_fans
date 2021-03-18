from django.conf.urls import include
from django.contrib.auth import login
from django.urls import path
from django.contrib import admin
from chat import views
from django.urls import path
from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chat/', include('chat.urls')),
    path('admin/', admin.site.urls),
    path('signup', views.signup,name='signup'),
    path('login',views.login,name='login'),
    path('home',views.home,name='home'),
    path('index',views.index),
    path('logout',views.logout),
    path('create_room',views.create_room),
    path('forgetpassword',views.forgetPassword),
    path('forgetpass',views.forget_pass,name='forgetpass'),
    path('save_room',views.saveRoom),
    path('rooms',views.allRooms),
    path('profile',views.profile),
    path('updateProfileImage',views.updateProfileImage,name='updateProfileImage'),
    path('updatePassword',views.updatePassword,name='updatePassword'),
    path('updateInfo',views.updateInfo,name='updateInfo'),
    path('search_room',views.search_room,name='search_room'), 
    path('add_admin',views.addAdmin,name='add_admin'),
    path('remove_admin',views.removeAdmin,name='remove_admin'),
    path('delete_user',views.removeMember,name='remove_member'), 
    path('join/<str:room_name>/', views.joinRoom, name='room_name'),
    path('room/<str:room_name>/', views.roomInfo, name='room_name'),     
    path('user/<str:user_name>/', views.userInfo, name='user_name'),
    path('edit/<str:room_name>/', views.editRoom, name='room_edit'),   

]

if settings.DEBUG:
     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


