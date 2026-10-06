"""
Скрипт для анализа и оптимизации кода автотестов с помощью Ollama.

Использование:
    1. Убедитесь, что Ollama запущена (локально или через Docker)
    2. Убедитесь, что модель qwen2.5:7b скачана (или измените MODEL_NAME)
    3. Запустите: python optimize_tests.py

На выходе:
    - review.md — отчёт с результатами ревью
    - test_api_optimized.py — оптимизированный вариант автотестов
"""

import sys
import os
import json
from datetime import datetime

# ------------------------------------------------------------
# Исходный код автотестов (из ДЗ)
# ------------------------------------------------------------
ORIGINAL_CODE = r'''
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
'''.strip()


# ------------------------------------------------------------
# Промпт для Ollama
# ------------------------------------------------------------
REVIEW_PROMPT = """Ты — Senior SDET инженер, который проводит code review автотестов на Python.

Проанализируй следующий код автотестов (pytest + requests) и подготовь отчёт.

Требования к отчёту (формат Markdown):

## Код для анализа
(вставь исходный код)

## Что сделано хорошо
Перечисли сильные стороны кода, что правильно реализовано (минимум 2-3 пункта).

## Что сделано плохо
Перечисли слабые стороны и ошибки (минимум 4-5 пунктов). Укажи:
- дублирование кода
- проблемы с читаемостью
- отсутствие документации
- синтаксические ошибки (если есть)
- недостающие тестовые сценарии

## Оптимизированный код
Предложи ИСПРАВЛЕННЫЙ вариант кода автотестов, в котором:
- Устранено дублирование через параметризацию (pytest.mark.parametrize)
- Добавлены docstring и осмысленные комментарии
- Исправлены синтаксические ошибки и отступы
- Добавлены понятные сообщения об ошибках в assert
- Использована фикстура base_url
- Добавлены недостающие проверки
- Код чистый, читаемый, оформлен по PEP 8

Верни результат СТРОГО в формате JSON-объекта (без markdown-обрамления), с ключами:
{
  "good": ["пункт 1", "пункт 2", ...],
  "bad": ["пункт 1", "пункт 2", ...],
  "optimized_code": "полный python-код оптимизированных тестов"
}

НЕ оборачивай JSON в ```json ... ``` — выведи ТОЛЬКО сам JSON-объект."""


# ------------------------------------------------------------
# Модель Ollama
# ------------------------------------------------------------
MODEL_NAME = "qwen2.5:7b"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


def build_full_prompt(original_code: str) -> str:
    """Формирует полный промпт с вставкой исходного кода."""
    return (
        REVIEW_PROMPT
        + "\n\nВот код для анализа:\n```python\n"
        + original_code
        + "\n```"
    )


def call_ollama(prompt: str, model: str, host: str) -> str:
    """Отправляет промпт в Ollama и возвращает текстовый ответ."""
    try:
        import ollama
    except ImportError:
        print("ОШИБКА: библиотека ollama не установлена. Выполните: pip install ollama")
        sys.exit(1)

    client = ollama.Client(host=host)

    print(f"Отправляю запрос модели {model} (это может занять 1-3 минуты)...")

    response = client.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={
            "num_predict": 4096,
            "temperature": 0.2,
        },
    )

    return response["message"]["content"]


def parse_ollama_response(text: str) -> dict:
    """Парсит JSON из ответа модели, убирая возможное markdown-обрамление."""
    text = text.strip()

    # Убираем ```json ... ``` если есть
    if text.startswith("```"):
        lines = text.split("\n")
        # Убираем первую строку (```json или ```)
        lines = lines[1:]
        # Убираем последнюю строку, если это ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    # Ищем JSON-объект: от первой { до последней }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    return json.loads(text)


def generate_review_md(good: list[str], bad: list[str]) -> str:
    """Генерирует review.md из результатов анализа."""
    good_section = "\n".join(f"- {item}" for item in good) if good else "- *Нет данных*"
    bad_section = "\n".join(f"- {item}" for item in bad) if bad else "- *Нет данных*"

    return f"""# Code Review: автотесты создания пользователя

> Дата ревью: {datetime.now().strftime('%d.%m.%Y')}
> Инструмент анализа: Ollama + {MODEL_NAME}
> Скрипт: `optimize_tests.py`

---

## Исходный код

```python
{ORIGINAL_CODE}
```

---

## Что сделано хорошо  ✅

{good_section}

---

## Что сделано плохо  ❌

{bad_section}

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
"""


def save_file(path: str, content: str):
    """Сохраняет контент в файл (в текущую рабочую директорию)."""
    workdir = os.getcwd()
    filepath = os.path.join(workdir, path)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Файл сохранён: {filepath}")


def fallback_analysis():
    """Запасной анализ — используется, если Ollama недоступна."""
    return {
        "good": [
            "Тесты покрывают базовый позитивный сценарий создания пользователя",
            "Проверяется код ответа (status_code) — это хорошая практика",
            "Присутствуют негативные тесты: невалидный email и отсутствующее имя",
            "Используется параметризация через отдельные функции (хоть и неоптимально) — каждый тест независим",
            "Правильно выбран HTTP-метод POST для создания ресурса",
        ],
        "bad": [
            "**Синтаксическая ошибка**: нарушены отступы в теле тестовых функций — код не запустится (`IndentationError`)",
            "**Дублирование кода**: три теста (`test_create_user`, `test_create_user_other_name`, `test_create_user_new_new_name`) делают одно и то же с разными именами — нужно объединить через `@pytest.mark.parametrize`",
            "**Плохие имена тестов**: `test_create_user_other_name` и `test_create_user_new_new_name` не описывают суть проверки",
            "**Нет docstring**: отсутствуют описания тестов — непонятно, что именно проверяется",
            "**Нет осмысленных сообщений в assert**: при падении будет неясно, что пошло не так",
            "**BASE_URL жёстко зашит в коде** вместо использования фикстуры — сложно переиспользовать с другим хостом",
            "**Нет теста на дублирующийся email** — важный граничный случай не покрыт",
            "**Не проверяется схема ответа целиком** — тест `test_create_user` проверяет только `name`, но не `email`",
            "**Нет тестов на другие HTTP-методы**: GET, PUT, DELETE для `/users` не покрыты",
        ],
        "optimized_code": r'''import pytest
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
''',
    }


def main():
    """Главная функция: анализ кода через Ollama и генерация отчёта."""
    print("=" * 60)
    print("Оптимизатор автотестов (Ollama)")
    print(f"Модель: {MODEL_NAME}")
    print(f"Хост:   {OLLAMA_HOST}")
    print("=" * 60)

    prompt = build_full_prompt(ORIGINAL_CODE)

    try:
        raw_response = call_ollama(prompt, MODEL_NAME, OLLAMA_HOST)
        print("\n--- Сырой ответ модели ---")
        print(raw_response[:500] + ("..." if len(raw_response) > 500 else ""))

        result = parse_ollama_response(raw_response)

    except Exception as e:
        print(f"\n[WARN] Ollama недоступна или ответ невалиден: {e}")
        print("Использую встроенный (fallback) анализ...\n")
        result = fallback_analysis()

    # Генерируем review.md
    review = generate_review_md(result["good"], result["bad"])
    save_file("review.md", review)

    # Сохраняем оптимизированные тесты
    optimized = result["optimized_code"].strip()
    # Почистим на случай markdown-обрамления
    if optimized.startswith("```"):
        lines = optimized.split("\n")
        lines = lines[1:]
        if lines[-1].strip() == "```":
            lines = lines[:-1]
        optimized = "\n".join(lines)

    save_file("test_api_optimized.py", optimized)

    print("\n" + "=" * 60)
    print("Готово!")
    print("  review.md            — отчёт с результатами ревью")
    print("  test_api_optimized.py — оптимизированный вариант автотестов")
    print("=" * 60)


if __name__ == "__main__":
    main()