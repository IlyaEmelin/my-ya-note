from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.test.client import Client

from notes.models import Note

User = get_user_model()


class TestRouter(TestCase):
    """Тестирование маршрутов"""

    @classmethod
    def setUpTestData(cls):
        """Установка тестовых данных"""
        cls.author = User.objects.create(username="Серега Пушкин")
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.user = User.objects.create(username="Иван Евтушенко")
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)

        cls.note = Note.objects.create(
            title="Заголовок",
            text="Текст",
            slug="slug_note",
            author=cls.author,
        )

        cls.url_notes_home = reverse(viewname="notes:home")
        cls.url_login = reverse("users:login")
        cls.url_users_login = reverse(viewname="users:login")
        cls.url_users_signup = reverse(viewname="users:signup")

        cls.url_notes_list = reverse(viewname="notes:list")
        cls.url_notes_add = reverse(viewname="notes:add")
        cls.url_notes_success = reverse(viewname="notes:success")
        cls.url_notes_edit = reverse(
            viewname="notes:edit",
            args=(cls.note.slug,),
        )
        cls.url_notes_detail = reverse(
            viewname="notes:detail",
            args=(cls.note.slug,),
        )
        cls.url_notes_delete = reverse(
            viewname="notes:delete",
            args=(cls.note.slug,),
        )

    def test_pages_anonymous_availability(self):
        """Проверка доступных страниц для анонимных пользователей"""
        urls = (
            self.url_notes_home,
            self.url_users_login,
            self.url_users_signup,
        )
        for url in urls:
            with self.subTest(name=url):
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
        urls = (
            self.url_notes_list,
            self.url_notes_add,
            self.url_notes_success,
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.FOUND,
                    msg=f"Удалось попасть на страницу: {url}",
                )
                redirect_url = f"{self.url_login}?next={url}"
                self.assertRedirects(
                    response,
                    redirect_url,
                    msg_prefix=(
                        "Не происходить "
                        f"редирект на страницу : {self.url_login}"
                    ),
                )

    def test_pages_authorized_user_availability(self):
        """Проверка доступности страниц авторизированным пользователям"""
        urls = (
            self.url_notes_home,
            self.url_notes_list,
            self.url_notes_add,
            self.url_notes_edit,
            self.url_notes_detail,
            self.url_notes_delete,
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    msg=f"Не удалось попасть на страницу: {url}",
                )

    def test_availability_for_note_detail_and_edit_and_delete(self):
        """Проверка доступности страниц заметок автору и пользователю"""
        for client, status in (
            (self.author_client, HTTPStatus.OK),
            (self.user_client, HTTPStatus.NOT_FOUND),
        ):
            for url in (
                self.url_notes_detail,
                self.url_notes_edit,
                self.url_notes_delete,
            ):
                with self.subTest(client=client, url=url):
                    response = client.get(url)
                    self.assertEqual(response.status_code, status)
