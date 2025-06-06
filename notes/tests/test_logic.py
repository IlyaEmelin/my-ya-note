from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note
from notes.pytest_tests.conftest import form_data

User = get_user_model()


class TestLogiCreate(TestCase):
    """Тестирование логики создания заметок"""

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username="Серега Пушкин")
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.url_notes_success = reverse("notes:success")
        cls.url_note_add = reverse("notes:add")

        cls.form_data = {
            "title": "Заголовок",
            "text": "Текс заметки",
            "slug": "slug",
        }

    def test_user_can_create_note(self):
        """Залогиненный пользователь может создавать заметки"""
        response = self.author_client.post(
            self.url_note_add,
            data=self.form_data,
        )

        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            msg=(
                "При создание заметки должен быть переход "
                "на страницу 'Завершено'",
            ),
        )
        self.assertRedirects(
            response,
            self.url_notes_success,
        )

        note_count = Note.objects.count()
        self.assertEqual(
            note_count,
            1,
            msg="Должна быть добавлена заметка в базу данных",
        )
        note = Note.objects.get()
        for key in self.form_data.keys():
            self.assertEqual(
                note.__dict__.get(key),
                self.form_data.get(key),
                msg=f"Не совпадают значения полей: {key}",
            )

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может добавлять заметки"""
        response = self.client.post(
            self.url_note_add,
            data=self.form_data,
        )

        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            msg=(
                "При создание заметки должен быть переход "
                "на страницу 'Завершено'",
            ),
        )
        self.assertRedirects(
            response,
            f"{reverse("users:login")}?next={self.url_note_add}",
        )

        note_count = Note.objects.count()
        self.assertEqual(
            note_count,
            0,
            msg="В базе не должно появиться записей",
        )

    def test_not_unique_slug(self):
        """Нельзя создать две заметки с одинаковым slug"""
        # Добавление первой заметки
        note = Note.objects.create(
            title="Заголовок 2",
            text="Текст заметки 2",
            slug="slug",
            author=self.author,
        )

        self.form_data["slug"] = "slug"
        # Добавление 2-й заметки
        response = self.author_client.post(
            self.url_note_add,
            data=self.form_data,
        )

        self.assertFormError(
            response.context["form"],
            "slug",
            errors=(note.slug + WARNING),
        )
        self.assertEqual(
            Note.objects.count(),
            1,
            msg=(
                "При добавление дубликата заметки по полю "
                "'slug'='slug' не должен добавляться."
            ),
        )

    def test_empty_slug(self):
        """Если не указан slug он, формируется самостоятельно"""

        form_data = self.form_data
        form_data.pop("slug")
        response = self.author_client.post(
            self.url_note_add,
            data=form_data,
        )

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, self.url_notes_success)
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data["title"])
        self.assertEqual(new_note.slug, expected_slug)


class TestLogicUpdateDelete(TestCase):
    """Тестирование логики изменение удаления заметок"""

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username="Серега Пушкин")

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.another = User.objects.create(username="Иван Евтушенко")
        cls.another_client = Client()
        cls.another_client.force_login(cls.another)

        cls.new_form_data = {
            "title": "Новый заголовок",
            "text": "Новый текс заметки",
            "slug": "new_default_slug",
        }
        cls.note = Note.objects.create(
            title="Заголовок",
            text="Текс заметки",
            slug="default_slug",
            author=cls.author,
        )

        cls.url_note_update = reverse(
            viewname="notes:edit",
            args=(cls.note.slug,),
        )
        cls.url_notes_success = reverse(viewname="notes:success")
        cls.url_notes_delete = reverse(
            viewname="notes:delete",
            args=(cls.note.slug,),
        )

    def test_author_can_edit_note(self):
        """Только автор может редактировать заметку"""
        response = self.author_client.post(
            self.url_note_update,
            data=self.new_form_data,
        )

        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            msg=(
                "После обновления должен быть "
                "переход на страницу завершения действия"
            ),
        )
        self.assertRedirects(response, self.url_notes_success)

        notes_count = Note.objects.count()
        self.assertEqual(
            notes_count,
            1,
            msg="После обновления должна остается так же одна запись а базе",
        )
        note = Note.objects.get(id=self.note.id)
        msg = "Значения поля должны совпадать{0}"
        self.assertEqual(
            note.title,
            self.new_form_data.get("title"),
            msg=msg.format("title"),
        )
        self.assertEqual(
            note.text,
            self.new_form_data.get("text"),
            msg=msg.format("text"),
        )
        self.assertEqual(
            note.slug,
            self.new_form_data.get("slug"),
            msg=msg.format("slug"),
        )

    def test_other_user_cant_edit_note(self):
        """Не автор не может редактировать заметку"""
        response = self.another_client.post(
            self.url_note_update,
            data=self.new_form_data,
        )

        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            msg="Обновлять чужие заметки запрещено",
        )
        note_from_db = Note.objects.get(id=self.note.id)
        msg = "Обновление не произошло поля должны совпадать{0}"
        self.assertEqual(
            self.note.title,
            note_from_db.title,
            msg.format("title"),
        )
        self.assertEqual(
            self.note.text,
            note_from_db.text,
            msg.format("text"),
        )
        self.assertEqual(
            self.note.slug,
            note_from_db.slug,
            msg.format("slug"),
        )

    def test_author_can_delete_note(self):
        """Не автор не может удалить"""
        response = self.author_client.post(self.url_notes_delete)
        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            msg=(
                "После удаления должен быть "
                "переход на страницу завершения действия"
            ),
        )
        self.assertEqual(
            Note.objects.count(),
            0,
            msg="После удаления в базе не должно остаться данных",
        )
        self.assertRedirects(response, self.url_notes_success)

    def test_other_user_cant_delete_note(self):
        """Не автор не может удалить заметку"""
        response = self.another_client.post(self.url_notes_delete)
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            msg="Удаление запрещено, поэтому страница не найдена",
        )
        self.assertEqual(
            Note.objects.count(),
            1,
            msg="Действие запрещено поэтому заметка осталась в базе",
        )
