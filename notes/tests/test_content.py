from django.db.models import QuerySet
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from notes.models import Note

User = get_user_model()


class TestNotesList(TestCase):
    """Тестирование страницы списка заметок"""

    NOTES_LIST_URL = reverse("notes:list")
    # так как нет не сортировки, не пейджинга
    # будем тестировать на 100-а заметок
    COUNT_NOTE = 100

    @classmethod
    def __gen_note(cls):
        """Генератор тестовых данных"""
        for i in range(cls.COUNT_NOTE):
            yield (
                ("title", f"Заметка {i}"),
                ("text", f"Текст заметки {i}"),
                ("slug", f"slug_{i}"),
                ("author", cls.author),
            )

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username="Серега Пушкин")
        cls.user = User.objects.create(username="Иван Евтушенко")

        all_notes = [Note(**dict(note_args)) for note_args in cls.__gen_note()]
        Note.objects.bulk_create(all_notes)

    def test_author_notes(self):
        """Тестирование списка заметок автора"""
        self.client.force_login(self.author)
        response = self.client.get(self.NOTES_LIST_URL)
        notes = response.context.get("object_list")

        self.assertIsInstance(notes, QuerySet)
        self.assertEqual(len(notes), self.COUNT_NOTE)
        data_tests = set(
            (
                ("title", note.title),
                ("text", note.text),
                ("slug", note.slug),
                ("author", note.author),
            )
            for note in notes
        )
        self.assertEqual(
            data_tests,
            set(self.__gen_note()),
            msg=(
                "Или не все данные добавлены в базу "
                "или не все данные получены из базы"
            ),
        )

    def test_user_notes(self):
        """Тестирование списка заметок автора"""
        self.client.force_login(self.user)
        response = self.client.get(self.NOTES_LIST_URL)
        notes = response.context.get("object_list")

        self.assertIsInstance(notes, QuerySet)
        self.assertEqual(
            len(notes),
            0,
            msg="Пользователь видит не свои заметки",
        )
