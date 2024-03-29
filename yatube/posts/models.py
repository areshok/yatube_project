from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Текст поста',
                            help_text='Введите текст поста',)
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='post',
                               verbose_name='Автор'
                               )
    group = models.ForeignKey(Group,
                              on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              related_name='post',
                              verbose_name='Группа',
                              help_text='Выберите группу',
                              )
    image = models.ImageField(verbose_name='Картинка',
                              upload_to='posts/',
                              blank=True,
                              )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:settings.TEXT_LIMIT]


class Comment(models.Model):

    text = models.TextField(verbose_name='Текст коментария',
                            help_text='Введите текст коментария',
                            )

    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Дата публикации коментария',
                                   )
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             verbose_name='Пост',
                             help_text='Текст коментария',
                             related_name='comment'
                             )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comment',
                               help_text='Автор коментария',
                               verbose_name='Автор коменария',
                               )

    def __str__(self):
        return self.author.username


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             help_text='Пользователь который подписывается',
                             verbose_name='Подписчик',
                             )

    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following',
                               help_text='На кого подписываются',
                               verbose_name='Автор',
                               )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follow')
        ]

    def __str__(self):
        return f'Пользователь {self.user} подписался на {self.author}'
