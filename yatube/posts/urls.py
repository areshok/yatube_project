from django.urls import path
from . import views

app_name = 'posts'


urlpatterns = [
    path('', views.index, name='index'),
    path('group/<slug:slug>/', views.group, name='group_list'),
    #path('fsdg_group/<slug:slug>/', views.group_post_detail, name='group'),
    ]
