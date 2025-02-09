from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestRoutes(TestCase):

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

    def test_home_availability_for_anonymous_user(self):
        url = reverse('note:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_access_for_authorized_user(self):
        self.client.force_login(self.reader)
        tested_urls = ('notes:list', 'notes:success', 'notes:add')
        for name in tested_urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)


class TestNotePermissions(TestCase):

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

    def test_notepage_permissions(self):
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


class TestRedirects(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.some_note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
            slug='test-slug'
        )

    def test_anonymous_user_redirect_to_login(self):
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


class TestNoteListContext(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.another_author = User.objects.create(username='Другой автор')
        cls.notes_by_author = [
            Note(
                title=f'Запись {i}',
                text='Текст',
                slug=f'slug_{i}',
                author=cls.author
            )
            for i in range(settings.NOTES_PER_PAGE + 1)
        ]
        cls.notes_by_other = [
            Note(
                title=f'Чужая запись {i}',
                text='Текст',
                slug=f'slug_other_{i}',
                author=cls.another_author
            )
            for i in range(settings.NOTES_PER_PAGE + 1)
        ]
        Note.objects.bulk_create(cls.notes_by_author + cls.notes_by_other)

    def test_note_appears_in_object_list(self):
        self.client.force_login(self.author)
        url = reverse('notes:list')
        response = self.client.get(url)
        notes_in_context = response.context['object_list']
        for note in self.notes_by_author:
            self.assertIn(note, notes_in_context)
        for note in self.notes_by_other:
            self.assertNotIn(note, notes_in_context)


class TestNoteFormContext(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.create_url = reverse('notes:add')

    def test_anonymous_client_has_no_form(self):
        response = self.client.get(self.create_url)
        self.assertNotIn('form', response.context)

    def test_authorized_client_has_form(self):
        self.client.force_login(self.author)
        response = self.client.get(self.create_url)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NoteForm)
