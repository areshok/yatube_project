from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow
from .utils import paginator

from django.views.decorators.cache import cache_page

@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    page_obj = paginator(post_list, request)
    context = {
        'page_obj': page_obj, }
    return render(request, 'posts/index.html', context)


def group(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.post.all()
    page_obj = paginator(posts, request)
    context = {
        'group': group,
        'page_obj': page_obj, }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    page_obj = paginator(user.post.all(), request)
    following =  user.following.exists()
    context = {
        'page_obj': page_obj,
        'author': user,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    count = Post.objects.filter(author=post.author).count()
    comments = Comment.objects.filter(post=post_id)
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'count': count,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post,
                    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
        'id': post.id}
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    # Получите пост и сохраните его в переменную post.
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    # ...
    user = request.user
    authors = user.follower.values_list('author', flat=True)
    posts_list = Post.objects.filter(author__id__in=authors)
    context = {'posts':posts_list}
    return render(request, 'posts/follow.html', context)

@login_required
def profile_follow(request, username):
    # Подписаться на автора
    auhtor = User.objects.get(username=username)
    user = request.user
    if auhtor != user:
        Follow.objects.create(user=user, author=auhtor)
        return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    user = request.user
    Follow.objects.get(user=user, author__username=username).delete()
    return redirect('posts:profile', username)
