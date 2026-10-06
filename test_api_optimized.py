import pytest
import requests


@pytest.fixture
def base_url():
    """Фикстура: базовый URL тестируемого API."""
    return "http://localhost:8000"


@pytest.mark.parametrize(
    "name, email",
    [
        ("Alice", "alice@example.com"),
        ("Bob", "bob@example.com"),
        ("Charlie", "charlie@example.com"),
    ],
)
def test_create_user_success(base_url, name, email):
    """Позитивный тест: создание пользователя возвращает 201 и корректные данные."""
    payload = {"name": name, "email": email}
    response = requests.post(f"{base_url}/users", json=payload)

    assert response.status_code == 201, (
        f"Ожидался статус 201, получен {response.status_code}"
    )

    data = response.json()
    assert data["name"] == name, (
        f"Ожидалось name={name!r}, получено {data.get('name')!r}"
    )
    assert data["email"] == email, (
        f"Ожидался email={email!r}, получен {data.get('email')!r}"
    )


def test_create_user_duplicate_email(base_url):
    """
    Негативный тест: повторное создание пользователя с тем же email
    должно вернуть ошибку (409 или 400).
    """
    payload = {"name": "Alice", "email": "alice@example.com"}
    # Первый запрос — создаём пользователя
    requests.post(f"{base_url}/users", json=payload)
    # Второй запрос — дубликат
    response = requests.post(f"{base_url}/users", json=payload)

    assert response.status_code in (400, 409), (
        f"Ожидался статус 400/409, получен {response.status_code}"
    )


@pytest.mark.parametrize(
    "payload, expected_status, description",
    [
        (
            {"name": "Test", "email": "bad-email"},
            400,
            "невалидный email",
        ),
        (
            {"email": "test@example.com"},
            400,
            "отсутствует поле name",
        ),
        (
            {"name": "Test"},
            400,
            "отсутствует поле email",
        ),
        (
            {"name": "", "email": "test@example.com"},
            400,
            "пустое имя",
        ),
        (
            {},
            400,
            "пустое тело запроса",
        ),
    ],
)
def test_create_user_validation_errors(base_url, payload, expected_status, description):
    """Параметризованный негативный тест: невалидные данные возвращают ошибку."""
    response = requests.post(f"{base_url}/users", json=payload)

    assert response.status_code == expected_status, (
        f"[{description}] Ожидался статус {expected_status}, "
        f"получен {response.status_code}, тело: {response.text}"
    )