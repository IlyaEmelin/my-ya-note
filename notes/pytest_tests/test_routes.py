from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_lazy_fixtures import lf

# @pytest.mark.parametrize(
#     "name",
#     (
#         "notes:home",
#         "users:login",
#         # "users:logout",  # Ошибка в уроках разлогирование не работает
#         "users:signup",
#     ),
# )
# def test_pages_availability_for_anonymous_user(client, name):
#     url = reverse(name)
#     response = client.get(url)
#     assert response.status_code == HTTPStatus.OK


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
