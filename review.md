# Code Review: автотесты создания пользователя

> Дата ревью: 06.10.2026
> Инструмент анализа: Ollama + qwen2.5:7b
> Скрипт: `optimize_tests.py`

---

## Исходный код

```python
import pytest
import requests

BASE_URL = "http://localhost:8000"

def test_create_user():
payload = {"name": "Alice", "email": "alice@example.com"}
response = requests.post(f"{BASE_URL}/users", json=payload)
assert response.status_code == 201
assert response.json()["name"] == "Alice"

def test_create_user_other_name():
payload = {"name": "Bob", "email": "bob@example.com"}
response = requests.post(f"{BASE_URL}/users", json=payload)
assert response.status_code == 201
assert response.json()["name"] == "Bob"

def test_create_user_new_new_name():
payload = {"name": "Charlie", "email": "charlie@example.com"}
response = requests.post(f"{BASE_URL}/users", json=payload)
assert response.status_code == 201
assert response.json()["name"] == "Charlie"

def test_create_user_invalid_email():
payload = {"name": "Test", "email": "bad-email"}
response = requests.post(f"{BASE_URL}/users", json=payload)
assert response.status_code == 400

def test_create_user_missing_name():
payload = {"email": "test@example.com"}
response = requests.post(f"{BASE_URL}/users", json=payload)
assert response.status_code == 400
```

---

## Что сделано хорошо  ✅

- Тесты покрывают базовый позитивный сценарий создания пользователя
- Проверяется код ответа (status_code) — это хорошая практика
- Присутствуют негативные тесты: невалидный email и отсутствующее имя
- Используется параметризация через отдельные функции (хоть и неоптимально) — каждый тест независим
- Правильно выбран HTTP-метод POST для создания ресурса

---

## Что сделано плохо  ❌

- **Синтаксическая ошибка**: нарушены отступы в теле тестовых функций — код не запустится (`IndentationError`)
- **Дублирование кода**: три теста (`test_create_user`, `test_create_user_other_name`, `test_create_user_new_new_name`) делают одно и то же с разными именами — нужно объединить через `@pytest.mark.parametrize`
- **Плохие имена тестов**: `test_create_user_other_name` и `test_create_user_new_new_name` не описывают суть проверки
- **Нет docstring**: отсутствуют описания тестов — непонятно, что именно проверяется
- **Нет осмысленных сообщений в assert**: при падении будет неясно, что пошло не так
- **BASE_URL жёстко зашит в коде** вместо использования фикстуры — сложно переиспользовать с другим хостом
- **Нет теста на дублирующийся email** — важный граничный случай не покрыт
- **Не проверяется схема ответа целиком** — тест `test_create_user` проверяет только `name`, но не `email`
- **Нет тестов на другие HTTP-методы**: GET, PUT, DELETE для `/users` не покрыты

---

## Сводная таблица

| Категория            | Оценка     | Комментарий                                                          |
|----------------------|------------|----------------------------------------------------------------------|
| Читаемость           | ⭐⭐☆☆☆      | Дублирование, плохие имена, нет документации                         |
| Структура            | ⭐⭐☆☆☆      | Копипаста трёх одинаковых тестов, нет параметризации                 |
| Покрытие сценариев   | ⭐⭐☆☆☆      | Только создание пользователя; нет других методов и граничных случаев |
| Обработка ошибок     | ⭐⭐⭐☆☆      | Базовые негативные тесты присутствуют                                |
| Соответствие PEP 8   | ⭐☆☆☆☆      | Нарушены отступы в теле функций (синтаксическая ошибка)             |
| Документирование     | ⭐☆☆☆☆      | Полностью отсутствуют docstring                                      |

---

## Рекомендации

1. Использовать `@pytest.mark.parametrize` для объединения однотипных тестов
2. Вынести `BASE_URL` в фикстуру `base_url`
3. Добавить docstring к каждому тесту с описанием проверяемого сценария
4. Добавить информативные сообщения в `assert` для упрощения отладки
5. Исправить отступы в теле тестовых функций
6. Добавить тесты: дублирующийся email, пустое имя, пустой email, неверный метод
7. Унифицировать имена тестов: придерживаться единого стиля `test_create_user_*`
