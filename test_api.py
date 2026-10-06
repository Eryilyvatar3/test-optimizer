import requests
import pytest

BASE_URL = "https://jsonplaceholder.typicode.com"

def test_get_post_1():
    """
    Тест 1 (контрактный): GET-запрос к эндпоинту /posts/1 - проверить, что статус-код ответа равен 200,
    а тело ответа содержит поля "userId", "id", "title", "body" правильных типов (userId и id - целые числа, title и body - строки).
    """
    response = requests.get(f"{BASE_URL}/posts/1")
    assert response.status_code == 200
    post_data = response.json()
    assert isinstance(post_data["userId"], int)
    assert isinstance(post_data["id"], int)
    assert isinstance(post_data["title"], str)
    assert isinstance(post_data["body"], str)

def test_post_new_post():
    """
    Тест 2 (функциональный): POST-запрос к эндпоинту /posts с телом {"title": "foo", "body": "bar", "userId": 1} -
    проверить, что статус-код ответа равен 201, и что в ответе содержатся те же значения полей "title",
    "body", "userId", которые были отправлены.
    """
    new_post_data = {"title": "foo", "body": "bar", "userId": 1}
    response = requests.post(f"{BASE_URL}/posts", json=new_post_data)
    assert response.status_code == 201
    created_post_data = response.json()
    for key, value in new_post_data.items():
        assert created_post_data[key] == value

def test_get_nonexistent_post():
    """
    Тест 3 (контрактный, негативный): GET-запрос к эндпоинту /posts/9999 (несуществующий id) -
    проверить, что статус-код ответа равен 404.
    """
    response = requests.get(f"{BASE_URL}/posts/9999")
    assert response.status_code == 404