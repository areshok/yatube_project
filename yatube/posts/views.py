from django.conf import settings
from django.shortcuts import get_object_or_404, render

from .models import Group, Post


def index(request):
    posts = Post.objects.all()[:settings.OUTPUT_LIMIT]
    context = {
        'posts': posts, }
    return render(request, 'posts/index.html', context)


def group(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.post.all()[:settings.OUTPUT_LIMIT]
    context = {
        'group': group,
        'posts': posts, }
    return render(request, 'posts/group_list.html', context)
