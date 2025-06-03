from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestLogiCreate(TestCase):
    """Тестирование логики создания заметок"""

    NOTE_ADD = reverse("notes:add")
    FORM_DATA = {
        "title": "Заголовок",
        "text": "Текс заметки",
        "slug": "slug",
    }

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username="Серега Пушкин")
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

    def test_create_node(self):
        """Создание заметок"""
        for client, http_status, count_node, redirect_url in (
            (
                self.client,
                HTTPStatus.FOUND,
                0,
                f"{reverse("users:login")}?next={self.NOTE_ADD}",
            ),
            (
                self.author_client,
                HTTPStatus.FOUND,
                1,
                reverse("notes:success"),
            ),
        ):
            with self.subTest(client=client, http_status=http_status):
                response = client.post(
                    self.NOTE_ADD,
                    data=self.FORM_DATA,
                )
                self.assertEqual(
                    response.status_code,
                    http_status,
                )
                self.assertRedirects(response, redirect_url)

                note_count = Note.objects.count()
                self.assertEqual(note_count, count_node)
                if count_node:
                    note = Note.objects.all()[0]
                    for key in self.FORM_DATA.keys():
                        self.assertEqual(
                            note.__dict__.get(key),
                            self.FORM_DATA.get(key),
                        )

    def test_not_unique_slug(self):
        """Нельзя создать две заметки с одинаковым slug"""
        # Добавление первой заметки
        note = Note.objects.create(
            title="Заголовок",
            text="Текст заметки",
            slug="slug",
            author=self.author,
        )

        # Добавление 2-й заметки
        response = self.author_client.post(
            self.NOTE_ADD,
            data=self.FORM_DATA,
        )
        self.assertFormError(
            response.context["form"],
            "slug",
            errors=(note.slug + WARNING),
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        new_form_data = dict(self.FORM_DATA)
        new_form_data.pop("slug")

        response = self.author_client.post(
            self.NOTE_ADD,
            data=new_form_data,
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse("notes:success"))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(new_form_data["title"])
        self.assertEqual(new_note.slug, expected_slug)


class TestLogicUpdateDelete(TestCase):
    """Тестирование логики изменение удаления заметок"""

    DEFAULT_SLUG = "slug"

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username="Серега Пушкин")

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.another = User.objects.create(username="Иван Евтушенко")
        cls.another_client = Client()
        cls.another_client.force_login(cls.another)

        cls.form_data = {
            "title": "Заголовок",
            "text": "Текс заметки",
            "slug": cls.DEFAULT_SLUG,
            "author": cls.author,
        }
        cls.note_update = reverse(
            "notes:edit",
            args=(cls.DEFAULT_SLUG,),
        )

        cls.note = Note.objects.create(**cls.form_data)

    def test_update_note(self):
        """Тестирование обновление заметки"""
        form_data = {
            "title": "Заголовок",
            "text": "Текс заметки",
            "slug": self.DEFAULT_SLUG,
            "author": self.author,
        }
        new_form_data = dict(form_data)
        new_form_data["title"] = "Новый заголовок"
        new_form_data["text"] = "Новый текст заметки"

        note_update = reverse(
            "notes:edit",
            args=(self.DEFAULT_SLUG,),
        )
        for client, http_status, update_data, redirect_url in (
            (
                self.client,
                HTTPStatus.FOUND,
                form_data,
                f"{reverse("users:login")}?next={note_update}",
            ),
            (
                self.another_client,
                HTTPStatus.NOT_FOUND,
                form_data,
                None,
            ),
            (
                self.author_client,
                HTTPStatus.FOUND,
                new_form_data,
                reverse("notes:success"),
            ),
        ):
            with self.subTest(client=client, http_status=http_status):
                response = client.post(
                    note_update,
                    data=new_form_data,
                )
                self.assertEqual(
                    response.status_code,
                    http_status,
                )
                if redirect_url:
                    self.assertRedirects(response, redirect_url)

                notes_count = Note.objects.count()
                self.assertEqual(notes_count, 1)
                note = Note.objects.all()[0]
                self.assertEqual(note.title, update_data.get("title"))
                self.assertEqual(note.text, update_data.get("text"))
                self.assertEqual(note.slug, update_data.get("slug"))
                self.assertEqual(note.author, update_data.get("author"))

    def test_delete_note(self):
        """Тестирование удаление заметки"""
        url = reverse(
            "notes:delete",
            args=(self.DEFAULT_SLUG,),
        )

        for client, result_count, http_status, redirect_url in (
            (
                self.client,
                1,
                HTTPStatus.FOUND,
                f"{reverse("users:login")}?next={url}",
            ),
            (
                self.another_client,
                1,
                HTTPStatus.NOT_FOUND,
                None,
            ),
            (
                self.author_client,
                0,
                HTTPStatus.FOUND,
                reverse("notes:success"),
            ),
        ):
            with self.subTest(client=client, http_status=http_status):
                response = client.post(url)

                self.assertEqual(
                    response.status_code,
                    http_status,
                )
                if redirect_url:
                    self.assertRedirects(response, redirect_url)

                notes_count = Note.objects.count()
                self.assertEqual(notes_count, result_count)
