from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.


def index(request):
    return HttpResponse('Главная страница')

def group_posts(request):
    return HttpResponse('Страница постов')


def group_post_detail(request, slug):
    return HttpResponse(f'Пост № {slug}')


