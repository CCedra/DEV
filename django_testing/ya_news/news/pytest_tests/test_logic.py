import pytest
from django.urls import reverse
from news.models import News, Comment
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_anonymous_user_cannot_comment(client):
    """Анонимный пользователь не может отправить комментарий."""
    news = News.objects.create(title="Тестовая новость", text="Несколько букв")
    url = reverse('news:detail', args=[news.pk])
    response = client.post(url, {'text': 'Комментарий'})
    assert response.status_code == 302


@pytest.mark.django_db
def test_authorized_user_can_comment(client):
    """Авторизованный пользователь может отправить комментарий."""
    user = User.objects.create_user(username="testuser", password="password")
    news = News.objects.create(title="Тестовая новость", text="Несколько букв")
    client.login(username='testuser', password='password')
    url = reverse('news:detail', args=[news.pk])
    response = client.post(url, {'text': 'Комментарий'})
    assert response.status_code == 302
    assert Comment.objects.count() == 1


@pytest.mark.django_db
def test_comment_with_bad_words_not_allowed(client):
    """
    Если комментарий содержит запрещённые слова,
    он не будет опубликован, а форма вернёт ошибку.
    """
    user = User.objects.create_user(username="testuser", password="password")
    news = News.objects.create(title="Тестовая новость", text="Несколько букв")

    client.login(username='testuser', password='password')
    url = reverse('news:detail', args=[news.pk])
    response = client.post(url, {'text': 'редиска!'})
    assert response.status_code == 200
    assert 'Не ругайтесь!' in str(response.content)


@pytest.mark.django_db
def test_authorized_user_can_edit_own_comment(client):
    """
    Авторизованный пользователь может редактировать
    или удалять свои комментарии.
    """
    user = User.objects.create_user(username="testuser", password="password")
    news = News.objects.create(title="Тестовая новость", text="Несколько букв")
    comment = Comment.objects.create(
        news=news,
        author=user,
        text="Старый комментарий"
    )

    client.login(username='testuser', password='password')
    url = reverse('news:edit', args=[comment.pk])
    response = client.post(url, {'text': 'Обновленный комментарий'})
    assert response.status_code == 302
    comment.refresh_from_db()
    assert comment.text == 'Обновленный комментарий'


@pytest.mark.django_db
def test_authorized_user_cannot_edit_others_comment(client):
    """
    Авторизованный пользователь не может редактировать
    или удалять чужие комментарии.
    """
    user1 = User.objects.create_user(username="user1", password="password")
    user2 = User.objects.create_user(username="user2", password="password")
    news = News.objects.create(title="Тествая новость", text="Несколько букв")
    comment = Comment.objects.create(
        news=news,
        author=user1,
        text="Оставленный комментарий"
    )
    client.login(username='user2', password='password')
    url = reverse('news:edit', args=[comment.pk])
    response = client.get(url)
    assert response.status_code == 404
