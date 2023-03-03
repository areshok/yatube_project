from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostCreateFormTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='testuser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='test_group',
            slug='test_group_slug',
            description='test_group_desc',
        )
        cls.post_1 = Post.objects.create(
            text='test_text_post_1',
            author=cls.user,
            group=cls.group,)

    def setUp(self):
        self.guest_client = self.client
        self.text = 'Текст поста'
        self.text_edit = 'edit_text'

    def test_create_post(self):
        """Валидная форма создает запись в Post.
        """
        post_count = Post.objects.count()

        form_data = {
            'text': self.text,
            'group': self.group.pk
        }

        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True)
        post_profile = reverse('posts:profile',
                               kwargs={'username': self.user.username})
        self.assertRedirects(response, post_profile)

        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.pk,
                text=self.text,
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post.
        """
        post_count = Post.objects.count()
        form_data = {
            'text': self.text_edit, }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post_1.id}),
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post_edit = Post.objects.get(id=self.post_1.id)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(post_edit.text, self.text_edit)

    def test_signup(self):
        """Проверка создание пользователя"""
        form_data = {
            'first_name': 'ars',
            'last_name': 'tur',
            'username': 'arstur1',
            'email': 'arstest@mail.ru',
            'password1': 'Ars123456789',
            'password2': 'Ars123456789',
        }
        response = self.guest_client.post(reverse('users:signup'),
                                          data=form_data,
                                          follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        user = User.objects.get(username=form_data['username'])
        self.assertTrue(user)
