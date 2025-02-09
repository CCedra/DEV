from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestPublicRoutes(TestCase):
    """Тест публичных маршрутов, доступных анонимным пользователям."""

    def test_home_availability_for_anonymous_user(self):
        """Главная страница доступна анонимному пользователю."""
        url = reverse('note:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_registration_and_login_available(self):
        """Страницы логина, регистрации и выхода доступны всем."""
        tested_urls = ('users:login', 'users:register', 'users:logout')
        for name in tested_urls:
            url = reverse(name)
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                HTTPStatus.OK,
                f'Страница {url} недоступна.'
            )


class TestNotePermissions(TestCase):
    """Тест доступа к страницам заметок."""

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Анон')
        cls.some_note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
            slug='test-slug'
        )

    def test_note_pages_access(self):
        """
        Тест доступа к отдельной заметке, редактированию и удалению.
        Только автор заметки может открыть эти страницы.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        tested_urls = ('notes:delete', 'notes:detail', 'notes:edit')
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in tested_urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.some_note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_access_for_authorized_user(self):
        """
        Авторизованный пользователь может заходить на страницы:
        - списка заметок (notes/)
        - успешного добавления (done/)
        - добавления заметки (add/)
        """
        self.client.force_login(self.reader)
        tested_urls = ('notes:list', 'notes:success', 'notes:add')
        for name in tested_urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)


class TestAuthRedirects(TestCase):
    """Тест редиректов анонимных пользователей."""

    @classmethod
    def setUpTestData(cls):
        cls.some_note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=User.objects.create(username='Автор'),
            slug='test-slug'
        )

    def test_anonymous_user_redirect_to_login(self):
        """
        Анонимного пользователя редиректит на логин при
        попытке зайти в приватные разделы.
        """
        login_url = reverse('users:login')
        tested_urls = (
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
            ('notes:delete', (self.some_note.slug,)),
            ('notes:detail', (self.some_note.slug,)),
            ('notes:edit', (self.some_note.slug,)),
        )
        for name, args in tested_urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertRedirects(response, f'{login_url}?next={url}')
