import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from news.models import News, Comment


@pytest.mark.django_db
def test_home_page_accessible_by_anonymous_user(client):
    """Проверка доступа главной страницы."""
    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_news_detail_page_accessible_by_anonymous_user(client):
    """Доступна ли страница с новостью анону."""
    news = News.objects.create(title="Тестовая новость", text="Пара букав")
    url = reverse('news:detail', args=[news.pk])
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_comment_delete_accessible_by_author_only(client):
    """Доступны ли страницы удаления и редактирования коммента его автору."""
    user = User.objects.create_user(username="testuser", password="password")
    news = News.objects.create(title="Тестовая новость", text="Пара букав")
    comment = Comment.objects.create(
        news=news,
        author=user,
        text="Комментарий пользователя"
    )

    # Анонимный пользователь
    url = reverse('news:delete', args=[comment.pk])
    response = client.get(url)
    assert response.status_code == 302

    # Авторизованный пользователь
    client.login(username='testuser', password='password')
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_comment_edit_accessible_by_author_only(client):
    """
    При попытке перейти на страницу редактирования или удаления комментария
    анонимный пользователь перенаправляется на страницу авторизации.
    """
    user = User.objects.create_user(username="testuser", password="password")
    news = News.objects.create(title="Тестовая новость", text="Пара букав")
    comment = Comment.objects.create(
        news=news,
        author=user,
        text="Комментарий пользователя"
    )

    # Анонимный пользователь
    url = reverse('news:edit', args=[comment.pk])
    response = client.get(url)
    assert response.status_code == 302

    # Авторизованный пользователь
    client.login(username='testuser', password='password')
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_comment_edit_not_allowed_for_other_users(client):
    """
    Авторизованный пользователь не может зайти на страницы редактирования
    или удаления чужих комментариев (возвращается ошибка 404).
    """
    user1 = User.objects.create_user(username="user1", password="password")
    user2 = User.objects.create_user(username="user2", password="password")
    news = News.objects.create(title="Тестовая новость", text="Пара букав")
    comment = Comment.objects.create(
        news=news,
        author=user1,
        text="Комментарий пользователя"
    )
    client.login(username='user2', password='password')
    url = reverse('news:edit', args=[comment.pk])
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_registration_and_login_pages_accessible_by_anonymous_user(client):
    """
    Страницы регистрации пользователей, входа в учётную запись и выхода
    из неё доступны анонимным пользователям.
    """
    url_register = reverse('account:register')
    url_login = reverse('account:login')
    url_logout = reverse('account:logout')

    response = client.get(url_register)
    assert response.status_code == 200

    response = client.get(url_login)
    assert response.status_code == 200

    response = client.get(url_logout)
    assert response.status_code == 302
