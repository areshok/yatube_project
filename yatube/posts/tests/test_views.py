import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEST_POSTS = 13

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPageTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # пользователь с постами
        cls.user = User.objects.create_user(username='testuser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        # пользователь подписчик
        cls.user_2 = User.objects.create_user(username='follower')
        cls.folower_client = Client()
        cls.folower_client.force_login(cls.user_2)

        cls.user_3 = User.objects.create_user(username='user_3')
        cls.user_3_folower = Client()
        cls.user_3_folower.force_login(cls.user_3)

        # не подписчик
        cls.user_no_f = User.objects.create(username='user_no_f')
        cls.user_no_f_cl = Client()
        cls.user_no_f_cl.force_login(cls.user_no_f)

        # csrf user
        cls.user_csrf = User.objects.create(username='user_csrf')
        cls.user_csrf_c = Client(enforce_csrf_checks=True)
        cls.user_csrf_c.force_login(cls.user_csrf)

        cls.group = Group.objects.create(
            title='test_group',
            slug='test_group_slug',
            description='test_group_desc',
        )
        cls.group_2 = Group.objects.create(
            title='test_group_2',
            slug='test_group_2_slug',
            description='test_group_2_desc',
        )
        # список для хранение созданных постов
        cls.posts_list = []

        cls.image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gpj',
            content=cls.image,
            content_type='image/jpg')

        for i in range(1, TEST_POSTS + 1):
            cls.posts_list.append(Post.objects.create(
                text=f'test_text_post_{i}',
                author=cls.user,
                group=cls.group,
                image=cls.uploaded,
            ))

    def setUp(self):
        super().setUp()
        self.guest_client = Client(enforce_csrf_checks=True)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_namespase_name_templates(self):
        """ Проверка namespace:name и шаблонов на соответсвие
        """
        templates_namespase = {
            'posts/index.html': reverse('posts:index'),

            'posts/group_list.html': reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}),

            'posts/profile.html': reverse(
                'posts:profile', kwargs={'username': self.user.username}),

            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': self.posts_list[0].id}),

            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_namespase.items():
            response = self.authorized_client.get(reverse_name)
            self.assertTemplateUsed(response, template)

    def test_namespase_name_templates_post_edit(self):
        """ Проверка namespace:name и шаблонов на соответсвие
            Отдельно тестируется posts_edit так как в словаре
            не может быть двух одинаковых ключей"""

        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.posts_list[0].id}))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def post_comparison(self,
                        post_id,
                        author_username,
                        post_text,
                        post_group):
        return [self.assertEqual(post_text, f'test_text_post_{post_id}'),
                self.assertEqual(author_username, self.user.username),
                self.assertEqual(post_group, self.group.title),
                self.assertEqual(post_id, self.posts_list[post_id - 1].id)]

    def test_correct_context_paginator(self):
        """Тест context и paginator index,group_list,profile
        """
        templates_namespase = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}),

            'posts/profile.html': reverse('posts:profile',
                                          kwargs={
                                              'username': self.user.username}),
        }
        for template, reverse_name in templates_namespase.items():
            response = self.authorized_client.get(reverse_name)
            # проверка context
            first_object = response.context['page_obj'][0]
            post_author_username = first_object.author.username
            post_text = first_object.text
            post_group = first_object.group.title
            post_id = first_object.id

            self.post_comparison(post_id,
                                 post_author_username,
                                 post_text,
                                 post_group,)
            # проверка paginator 1 страница
            self.assertEqual(len(response.context['page_obj']),
                             settings.OUTPUT_LIMIT)
            # проверка paginator 2 страница
            response = self.authorized_client.get(reverse_name + '?page=2')
            self.assertEqual(len(response.context['page_obj']),
                             TEST_POSTS - settings.OUTPUT_LIMIT)

    def test_context_post_detail(self):
        """Тест context на post_detail
        """
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.posts_list[0].id}))
        post_author = response.context['post'].author.username
        post_text = response.context['post'].text
        post_group = response.context['post'].group.title
        post_id = response.context['post'].id
        self.post_comparison(post_id,
                             post_author,
                             post_text,
                             post_group)

    def test_context_post_edit(self):
        """ Тест context post edit
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.posts_list[0].id}))
        post_text = response.context['form']['text'].value()
        post_group = response.context['form']['group'].value()
        self.assertEqual(post_text, self.posts_list[0].text)
        self.assertEqual(post_group, self.group.id)

    def test_context_post_create(self):
        """ Тест context post create
        """
        response = self.authorized_client.get(reverse('posts:post_create'))
        post_text = response.context['form']['text'].value()
        post_group = response.context['form']['group'].value()
        self.assertEqual(post_text, None)
        self.assertEqual(post_group, None)

    def test_post_no_group_2(self):
        """ Проверка что созданный пост для группы 1 не попадет в группу 2
        """
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_2.slug}))
        posts = len(response.context['page_obj'])
        self.assertEqual(posts, 0)

    def test_image_index_profile_group(self):
        """ Проверка на наличии картинки в постах
        """
        reverse_name_list = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.user.username}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:post_detail',
                    kwargs={'post_id': self.posts_list[-1].id}),
        ]
        for reverse_name in reverse_name_list:
            response = self.authorized_client.get(reverse_name)
            self.assertContains(response, '<img')

    def test_image_detail(self):
        """ Проверка наличие картинки в посте
        """
        reverse_name = reverse('posts:post_detail',
                               kwargs={'post_id': self.posts_list[-1].id})
        response = self.authorized_client.get(reverse_name)
        self.assertContains(response, '<img')

    def test_follow_page_and_paginator(self):
        """ Тест posts:follow_index и paginator
        """
        Follow.objects.create(user=self.user_2, author=self.user)
        reverse_name = reverse('posts:follow_index')
        response = self.folower_client.get(reverse('posts:follow_index'))
        # проверка получение перого поста на подписанного автора
        first_object = response.context['page_obj'][0]
        post_author_username = first_object.author.username
        self.assertEqual(post_author_username, self.user.username),
        # проверка paginator 1 страница
        self.assertEqual(len(response.context['page_obj']),
                         settings.OUTPUT_LIMIT)
        # проверка paginator 2 страница
        response = self.folower_client.get(reverse_name + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         TEST_POSTS - settings.OUTPUT_LIMIT)

        # тест не подписчика
        response = self.user_no_f_cl.get(reverse('posts:follow_index'))
        posts_list = response.context['page_obj']
        self.assertEqual(len(posts_list), 0)

    def test_follow(self):
        """Тестирование подписки
        """
        follow = self.user_2.follower.count()
        self.assertEqual(follow, 0, 'должно быть ноль подписок у пользователя')

        # подписываемся на 2 пользователей
        self.folower_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}))
        # проверяем есть ли подписка
        self.assertTrue(Follow.objects.filter(
            user=self.user_2, author=self.user).exists())

    def test_unfollow(self):
        """Тест описки
        """
        Follow.objects.create(user=self.user, author=self.user_2)
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=self.user_2).exists())

        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user_2.username}))

        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.user_2).exists())

    def test_cache(self):
        """ Проверка кеша на index
        """
        reverse_name = reverse('posts:index')
        response = self.authorized_client.get(reverse_name)
        posts = response.content
        # удаление из бд последнего поста
        Post.objects.order_by('-pk')[0].delete()
        # проверка № последнего поста и подсчет списка постов созданных вначале
        old_response = self.authorized_client.get(reverse_name)
        old_posts = old_response.content
        # проверка на совпадение
        self.assertEqual(old_posts, posts)
        # чистим кеш
        cache.clear()
        # новый запрос
        new_response = self.authorized_client.get(reverse_name)
        new_posts = new_response.content
        # проверка на несовпадение
        self.assertNotEqual(old_posts, new_posts)

    def test_custom_template_error(self):
        response = self.guest_client.post('/')
        self.assertTemplateUsed(response, 'core/403csrf.html')

        response = self.guest_client.get('/404/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')
