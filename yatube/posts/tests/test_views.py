from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

TEST_POSTS = 13


class PostPageTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.user = User.objects.create_user(username='testuser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

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

    def setUp(self):
        for i in range(1, TEST_POSTS + 1):
            self.posts_list.append(Post.objects.create(
                text=f'test_text_post_{i}',
                author=self.user,
                group=self.group,
            ))

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
