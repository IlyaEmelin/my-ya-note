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
        cls.notes_list_url = reverse("notes:list")

        cls.author = User.objects.create(username="Серега Пушкин")
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.user = User.objects.create(username="Иван Евтушенко")
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)

        # all_notes = [Note(**dict(note_args)) for note_args in cls.__gen_note()]
        # Note.objects.bulk_create(all_notes)
        cls.note = Note.objects.create(
            title="Заголовок",
            text="Текст заметки",
            slug="note-slug",
            author=cls.author,
        )

    def test_notes_list_for_different_users(self):
        """Тестирование списка заметок для разных авторов"""
        for client, note_in_list in (
            (self.author_client, True),
            (self.user_client, False),
        ):
            with self.subTest(client=client, note_in_list=note_in_list):
                response = client.get(self.notes_list_url)
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
        for name, args in (
            ("notes:add", None),
            ("notes:edit", (self.note.slug,)),
        ):
            response = self.author_client.get(reverse(name, args=args))

            self.assertIn(
                "form",
                response.context,
                msg=(
                    "на страницы создания и редактирования заметки "
                    "передаются формы."
                ),
            )
