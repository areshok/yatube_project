from django.conf import settings
from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post_1 = Post.objects.create(
            author=cls.user,
            text='Тестовый пост' * 10,
        )

    def test_models_have_correct_object_names(self):
        """Проверка правильного отображения поля __str__ у моделей.
        """

        group = PostModelTest.group
        expected_object_name_group = group.title
        self.assertEqual(expected_object_name_group, str(group))

        post = PostModelTest.post_1
        post_lenght = len(str(post))
        self.assertEqual(post_lenght, settings.TEXT_LIMIT)
        self.assertEqual(post.text[:settings.TEXT_LIMIT], str(post))
