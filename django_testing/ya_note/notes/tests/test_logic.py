from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('note:edit', args=(cls.notes.slug))
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.create_url = reverse('note:create')
        cls.form_data = {
            'title': 'Тестовый заголовок',
            'text': 'Сам текст',
            'slug': 'test_slug_note_create'
        }

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        note_count_before = Note.objects.count()
        self.client.post(self.create_url, data=self.form_data)
        note_count_after = Note.objects.count()
        self.assertEqual(note_count_before, note_count_after)

    def test_user_can_create_comment(self):
        """Авторизованный пользователь может создать заметку."""
        response = self.auth_client.post(self.create_url, data=self.form_data)
        self.assertRedirects(response, reverse('note:list'))
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.user)


class TestUniqueSlug(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='Пользователь')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.create_url = reverse('note:create')
        cls.slug = 'non_unique_slug'
        cls.note = Note.objects.create(
            title='Новая заметка',
            text='Текст новой заметки',
            slug=cls.slug,
            author=cls.user
        )
        cls.form_data = {
            'title': 'Не новая заметка',
            'text': 'Текст не новой заметки',
            'slug': cls.slug,
        }

    def test_cannot_create_note_with_duplicate_slug(self):
        """Проверяем, что нельзя создать две заметки с одинаковым slug."""
        note_count_before = Note.objects.count()
        response = self.auth_client.post(self.create_url, data=self.form_data)
        note_count_after = Note.objects.count()
        self.assertEqual(note_count_before, note_count_after)
        self.assertFormError(
            response,
            'form',
            'slug',
            'Заметка с таким Slug уже существует.'
        )


class TestAutoSlug(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='Автор')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        cls.create_url = reverse('note:create')

        cls.title = 'Тестовая заметка'
        cls.form_data = {
            'title': cls.title,
            'text': 'Какой-то текст',
            'slug': '',
        }

    def test_slug_is_generated_automatically(self):
        """Если slug не указан, он должен сформироваться автоматически."""
        self.auth_client.post(self.create_url, data=self.form_data)
        note = Note.objects.get()
        expected_slug = slugify(self.title)
        self.assertEqual(note.slug, expected_slug)
        self.assertEqual(note.title, self.title)
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.author, self.user)


class TestNotePermissions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='Автор')
        cls.other_user = User.objects.create_user(username='Другой автор')
        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Какой-то текст',
            slug='test-slug',
            author=cls.user
        )
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.other_client = Client()
        cls.other_client.force_login(cls.other_user)
        cls.edit_url = reverse('note:edit', args=[cls.note.slug])
        cls.delete_url = reverse('note:delete', args=[cls.note.slug])
        cls.new_data = {
            'title': 'Обновлённая заметка',
            'text': 'Обновлённый текст',
            'slug': 'test-slug'
        }

    def test_user_can_edit_own_note(self):
        """Автор заметки может её редактировать."""
        response = self.auth_client.post(self.edit_url, data=self.new_data)
        self.note.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.note.title, self.new_data['title'])
        self.assertEqual(self.note.text, self.new_data['text'])

    def test_user_cant_edit_someone_elses_note(self):
        """Чужой пользователь не может редактировать чужую заметку."""
        response = self.other_client.post(self.edit_url, data=self.new_data)

        self.note.refresh_from_db()
        self.assertNotEqual(self.note.title, self.new_data['title'])
        self.assertEqual(response.status_code, 403)

    def test_user_can_delete_own_note(self):
        """Автор заметки может её удалить."""
        response = self.auth_client.post(self.delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Note.objects.filter(slug=self.note.slug).exists())

    def test_user_cant_delete_someone_elses_note(self):
        """Чужой пользователь не может удалить чужую заметку."""
        response = self.other_client.post(self.delete_url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Note.objects.filter(slug=self.note.slug).exists())
