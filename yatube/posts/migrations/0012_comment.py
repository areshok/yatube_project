# Generated by Django 2.2.19 on 2023-03-11 13:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('posts', '0011_post_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(help_text='Введите текст коментария', verbose_name='Текст коментария')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации коментария')),
                ('author', models.ForeignKey(help_text='Автор коментария', on_delete=django.db.models.deletion.CASCADE, related_name='comments', to=settings.AUTH_USER_MODEL, verbose_name='Автор коменария')),
                ('post', models.ForeignKey(help_text='Текст коментария', on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='posts.Post', verbose_name='Пост')),
            ],
        ),
    ]
