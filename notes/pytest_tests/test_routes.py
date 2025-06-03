from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_lazy_fixtures import lf
from pytest_django.asserts import assertRedirects

@pytest.mark.parametrize(
    "parametrized_client, expected_status",
    (
        (lf("not_author_client"), HTTPStatus.NOT_FOUND),
        (lf("author_client"), HTTPStatus.OK),
    ),
)
@pytest.mark.parametrize(
    "name",
    ("notes:detail", "notes:edit", "notes:delete"),
)
def test_pages_availability_for_different_users(
    parametrized_client, name, note, expected_status
):
    url = reverse(name, args=(note.slug,))
    response = parametrized_client.get(url)
    assert response.status_code == expected_status

@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:detail', lf('slug_for_args')),
        ('notes:edit', lf('slug_for_args')),
        ('notes:delete', lf('slug_for_args')),
        ('notes:add', None),
        ('notes:success', None),
        ('notes:list', None),
    ),
)
# Передаём в тест анонимный клиент, name проверяемых страниц и args:
def test_redirects(client, name, args):
    login_url = reverse('users:login')
    # Теперь не надо писать никаких if и можно обойтись одним выражением.
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)