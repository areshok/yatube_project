import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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
        self.image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.image,
            content_type='image/gif')

        self.path_to_file = 'posts/small.gif'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post.
        """
        post_count = Post.objects.count()

        form_data = {
            'text': self.text,
            'group': self.group.pk,
            'image': self.uploaded,
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
                image=self.path_to_file,
            ).exists()
        )
        cache.clear()

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

    def test_comment(self):
        """Проверка создание коммента и получение его
        """
        form_data = {
            'text': 'тестовый комент'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post_1.id}),
            data=form_data, follow=True)
        resp_get = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_1.id}))
        context = resp_get.context['comments'][0]
        self.assertEqual(context.text, form_data['text'])
