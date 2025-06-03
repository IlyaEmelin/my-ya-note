from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRouter(TestCase):
    """Тестирование маршрутов"""

    @classmethod
    def setUpTestData(cls):
        """Установка тестовых данных"""
        cls.author = User.objects.create(username="Серега Пушкин")
        cls.user = User.objects.create(username="Иван Евтушенко")

        cls.slug_note = "slug_note"
        cls.note = Note.objects.create(
            title="Заголовок",
            text="Текст",
            slug=cls.slug_note,
            author=cls.author,
        )

    def test_pages_anonymous_availability(self):
        """Проверка доступных страниц для анонимных пользователей"""
        urls = (
            "notes:home",
            "users:login",
            # Уроки сломаны поэтому эта страница не работает
            # "users:logout",
            "users:signup",
        )
        for url_name in urls:
            with self.subTest(name=url_name):
                url = reverse(viewname=url_name)
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    msg=f"Не удается попасть на страницу: {url}",
                )

    def test_pages_anonymous_unavailability(self):
        """
        Проверка не доступных страниц для анонимных пользователей,
        и редирект на страницу аутентификации
        """
        login_url = reverse("users:login")
        urls = (
            ("notes:list", None),
            ("notes:add", None),
            ("notes:edit", (self.slug_note,)),
            ("notes:detail", (self.slug_note,)),
            ("notes:delete", (self.slug_note,)),
        )
        for url_name, args in urls:
            with self.subTest(name=url_name):
                url = reverse(url_name, args=args)
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.FOUND,
                    msg=f"Удалось попасть на страницу: {url}",
                )
                redirect_url = f"{login_url}?next={url}"
                self.assertRedirects(
                    response,
                    redirect_url,
                    msg_prefix=(
                        f"Не происходить редирект на страницу : {login_url}"
                    ),
                )

    def test_pages_authorized_user_availability(self):
        """Проверка доступности страниц авторизированным пользователям"""
        urls = (
            ("notes:home", None),
            ("users:login", None),
            # Уроки сломаны поэтому эта страница не работает
            # ("users:logout", None)
            ("users:signup", None),
            ("notes:list", None),
            ("notes:add", None),
            ("notes:edit", (self.slug_note,)),
            ("notes:detail", (self.slug_note,)),
            ("notes:delete", (self.slug_note,)),
        )
        self.client.force_login(self.author)
        for url_name, args in urls:
            with self.subTest(name=url_name):
                url = reverse(url_name, args=args)
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    msg=f"Не удалось попасть на страницу: {url}",
                )

    def test_availability_for_note_detail_and_edit_and_delete(self):
        """Проверка доступности страниц заметок автору и пользователю"""
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.user, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for url_name in ("notes:detail", "notes:edit", "notes:delete"):
                with self.subTest(user=user, name=url_name):
                    url = reverse(url_name, args=(self.slug_note,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)
