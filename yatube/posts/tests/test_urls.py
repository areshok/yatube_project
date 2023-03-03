from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # авторизированный пользователь 1
        cls.user = User.objects.create_user(username='testuser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        # авторизированный пользователь 2
        cls.user_2 = User.objects.create_user(username='user_2')
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.user_2)
        # группа
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_group_slug',
            description='test_group_desc',
        )
        # пост
        cls.post = Post.objects.create(
            text='test_text_post',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        # неавторизированный пользователь
        self.guest_client = self.client

    def test_status_code_all_users(self):
        '''Доступность страниц для всех пользователей
        Проверяет доступ к: Домашней странице,
                            Неизвестной странице,
                            Страница Группы,
                            Страница Профиля,
                            Страница Поста
        '''
        status_code_url = {
            '/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,

        }
        for address, code in status_code_url.items():
            with self.subTest(address=address):
                # для гостя
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, code)
                # для авторизированого пользователя
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, code)

    def test_urls_all_users_template(self):
        '''URL-адрес использует соответствующий шаблон.
        '''
        templates_url_names_all = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.user.username}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
        }
        for template, address in templates_url_names_all.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_create_login_user(self):
        """Создание поста авторизованным пользователем РАЗРЕШЕНО
        """
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_anonim_user(self):
        """Создание поста анонимным пользователем ЗАПРЕЩЕНО:
        Перенаправляет на страницу входа
        """
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_author(self):
        """Редактирование поста автором РАЗРЕШЕНО:
        """
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_no_author(self):
        """Редактирование поста не автором ЗАПРЕЩЕНО:
        """
        response = self.authorized_client_2.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_post_edit_anonim_user(self):
        """Редактирование поста анонимным пользователем ЗАПРЕЩЕНО:
        """
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response,
                             '/auth/login/?next=%2Fposts%2F1%2Fedit%2F')

    def test_login_page(self):
        response = self.guest_client.get('/auth/login/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
