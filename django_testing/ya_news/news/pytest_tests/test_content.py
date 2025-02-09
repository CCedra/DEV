import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from news.models import News, Comment

from yanews.settings import NEWS_PER_PAGE

User = get_user_model()


@pytest.mark.django_db
def test_home_page_has_no_more_than_10_news(client):
    """Количество новостей на главной странице не более 10."""
    for i in range(15):
        News.objects.create(title=f"Новость номер {i}", text="Несоклько букв")

    url = reverse('news:home')
    response = client.get(url)

    news = response.context['news_list']
    assert len(news) <= NEWS_PER_PAGE


@pytest.mark.django_db
def test_news_are_sorted_by_date(client):
    """
    Новости отсортированы от самой свежей к самой старой.
    Свежие новости в начале списка.
    """
    News.objects.create(
        title="Старая новость",
        text="Это очень старая новость",
        date="2023-01-01"
    )
    News.objects.create(
        title="Свежая новость",
        text="Самая свежая новость",
        date="2025-01-01"
    )

    url = reverse('news:home')
    response = client.get(url)

    news_titles = [news.title for news in response.context['news_list']]
    assert news_titles == ['New News', 'Old News']


@pytest.mark.django_db
def test_comments_sorted_by_creation_date(client):
    """
    Комментарии на странице отдельной новости отсортированы в хронологическом
    порядке: старые в начале списка, новые — в конце.
    """
    user = User.objects.create_user(username="testuser", password="password")
    news = News.objects.create(title="Тестовая новость", text="Несколько букв")
    comment1 = Comment.objects.create(
        news=news,
        author=user,
        text="Первый!"
    )
    comment2 = Comment.objects.create(
        news=news,
        author=user,
        text="Второй..."
    )

    url = reverse('news:detail', args=[news.pk])
    response = client.get(url)

    comments = response.context['news'].comment_set.all()
    assert list(comments) == [comment1, comment2]


@pytest.mark.django_db
def test_comment_form_visibility(client):
    """
    Анонимному пользователю недоступна форма для отправки комментария
    на странице отдельной новости, а авторизованному доступна.
    """
    User.objects.create_user(username="testuser", password="password")
    news = News.objects.create(title="Тестовая новость", text="Несколько букв")

    # Анонимный пользователь
    url = reverse('news:detail', args=[news.pk])
    response = client.get(url)
    assert 'form' not in response.context

    # Авторизованный пользователь
    client.login(username='testuser', password='password')
    response = client.get(url)
    assert 'form' in response.context
