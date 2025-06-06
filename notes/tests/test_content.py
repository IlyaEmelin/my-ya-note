from django.db.models import QuerySet
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client

from notes.models import Note

User = get_user_model()


class TestNotesList(TestCase):
    """Тестирование страницы списка заметок"""

    @classmethod
    def setUpTestData(cls):

        cls.author = User.objects.create(username="Серега Пушкин")
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.user = User.objects.create(username="Иван Евтушенко")
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)

        cls.note = Note.objects.create(
            title="Заголовок",
            text="Текст заметки",
            slug="note-slug",
            author=cls.author,
        )

        cls.url_notes_list = reverse("notes:list")
        cls.url_notes_add = reverse("notes:add")
        cls.url_notes_edit = reverse(
            viewname="notes:edit",
            args=(cls.note.slug,),
        )

    def test_notes_list_for_different_users(self):
        """Тестирование списка заметок для разных авторов"""
        for client, note_in_list in (
            (self.author_client, True),
            (self.user_client, False),
        ):
            with self.subTest(client=client, note_in_list=note_in_list):
                response = client.get(self.url_notes_list)
                notes = response.context.get("object_list")

                self.assertIsInstance(
                    notes,
                    QuerySet,
                    msg=(
                        "Список заметок должен быть "
                        "соответствующего типа данных"
                    ),
                )
                self.assertEqual(
                    self.note in notes,
                    note_in_list,
                    msg="Не корректно видит список заметок",
                )

    def test_pages_contains_form(self):
        """Тестирование форм создания и редактирования заметки"""
        for url in (
            self.url_notes_add,
            self.url_notes_edit,
        ):
            with self.subTest(url=url):
                response = self.author_client.get(url)

                self.assertIn(
                    "form",
                    response.context,
                    msg=(
                        "на страницы создания и редактирования заметки "
                        "передаются формы."
                    ),
                )
