# test_logic.py
import pytest

from pytest_django.asserts import assertRedirects, assertFormError
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING


def test_user_can_create_note(author_client, author, form_data):
    """Залогиненный пользователь может создавать заметки"""
    url = reverse("notes:add")
    response = author_client.post(url, data=form_data)

    assertRedirects(response, reverse("notes:success"))

    assert Note.objects.count() == 1
    new_note = Note.objects.get()
    assert new_note.title == form_data["title"]
    assert new_note.text == form_data["text"]
    assert new_note.slug == form_data["slug"]
    assert new_note.author == author


@pytest.mark.django_db
def test_anonymous_user_cant_create_note(client, form_data):
    """Анонимный клиент не может создавать заметки"""
    url = reverse("notes:add")
    response = client.post(url, data=form_data)
    login_url = reverse("users:login")
    expected_url = f"{login_url}?next={url}"
    assertRedirects(response, expected_url)
    assert Note.objects.count() == 0


def test_not_unique_slug(author_client, note, form_data):
    """Нельзя создать две заметки с одинаковым slug"""
    url = reverse("notes:add")
    form_data["slug"] = note.slug
    response = author_client.post(url, data=form_data)
    assertFormError(
        response.context["form"],
        "slug",
        errors=(note.slug + WARNING),
    )
    assert Note.objects.count() == 1
