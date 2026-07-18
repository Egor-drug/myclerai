# generate.py

import aiohttp
import asyncio
import re
from config import AI_TOKEN

OPENROUTER_API_KEY = AI_TOKEN
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ЕДИНАЯ МОДЕЛЬ
MODEL = "openrouter/free"


async def generate(text: str, fast: bool = True) -> str:
    """
    Генерирует ответ через OpenRouter

    fast=True - быстрый ответ (краткий, по делу)
    fast=False - углубленный ответ (подробный, структурированный)
    """

    # Формируем системный промпт в зависимости от режима
    if fast:
        system_prompt = """Ты - полезный помощник. Отвечай кратко, четко и по делу.
Используй понятный язык. Структурируй ответ, если это необходимо для понимания.
Не углубляйся в лишние детали. Дай только самую важную информацию."""
        temperature = 0.7
        max_tokens = 1000
    else:
        system_prompt = """Ты - экспертный помощник по решению учебных заданий. 
Дай максимально подробный, структурированный и глубокий ответ.

Требования к углубленному ответу:
1. Раскрой тему максимально полно
2. Приведи пошаговое решение или объяснение
3. Объясни ключевые понятия и термины
4. Приведи примеры для лучшего понимания
5. Сделай вывод или резюме в конце
6. Используй четкую структуру (пункты, подпункты, нумерацию)
7. Будь максимально полезным и информативным
8. Используй форматирование для улучшения читаемости (жирный, курсив, списки)"""
        temperature = 0.5
        max_tokens = 3000

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    timeout = aiohttp.ClientTimeout(total=15 if fast else 45)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout) as response:

                if response.status == 429:
                    print(f"⚠️ Rate-limited")
                    return "⏳ Слишком много запросов. Подождите немного."

                if response.status != 200:
                    print(f"Ошибка API: {response.status}")
                    return f"❌ Ошибка сервера (код {response.status}). Попробуйте позже."

                result = await response.json()

                if 'choices' not in result or not result['choices']:
                    return "❌ Не удалось получить ответ. Попробуйте ещё раз."

                answer = result['choices'][0]['message'].get('content', '')

                if answer:
                    # Очистка HTML и форматирование
                    answer = re.sub(r'<h[1-6]>(.*?)</h[1-6]>', r'\n**\1**\n', answer, flags=re.IGNORECASE | re.DOTALL)
                    answer = re.sub(r'<b>(.*?)</b>', r'**\1**', answer, flags=re.IGNORECASE | re.DOTALL)
                    answer = re.sub(r'<strong>(.*?)</strong>', r'**\1**', answer, flags=re.IGNORECASE | re.DOTALL)
                    answer = re.sub(r'<i>(.*?)</i>', r'*\1*', answer, flags=re.IGNORECASE | re.DOTALL)
                    answer = re.sub(r'<em>(.*?)</em>', r'*\1*', answer, flags=re.IGNORECASE | re.DOTALL)
                    answer = re.sub(r'<br\s*/?>', '\n', answer, flags=re.IGNORECASE)
                    answer = re.sub(r'<p>(.*?)</p>', r'\1\n', answer, flags=re.IGNORECASE | re.DOTALL)
                    answer = re.sub(r'<[^>]+>', '', answer)
                    answer = re.sub(r'\n{3,}', '\n\n', answer)

                    # Дополнительная очистка для красивого вывода
                    answer = re.sub(r'^\s+', '', answer, flags=re.MULTILINE)
                    answer = re.sub(r'\s+$', '', answer, flags=re.MULTILINE)

                return answer.strip() if answer else "❌ Пустой ответ от модели. Попробуйте ещё раз."

    except asyncio.TimeoutError:
        if fast:
            return "⏰ Время ожидания истекло. Попробуйте использовать углубленный режим (🐢)."
        else:
            return "⏰ Углубленный ответ занимает много времени. Попробуйте использовать быстрый режим (⚡) или повторите позже."
    except aiohttp.ClientError as e:
        print(f"Client error: {e}")
        return "❌ Ошибка соединения. Проверьте интернет-соединение."
    except Exception as e:
        print(f"Generate error: {e}")
        return f"❌ Произошла ошибка: {str(e)[:100]}"


# Вспомогательные функции для очистки текста
def clean_response_text(text: str) -> str:
    """Дополнительная очистка ответа от лишних символов"""
    if not text:
        return ""

    # Удаляем лишние пробелы в начале и конце
    text = text.strip()

    # Убираем множественные переносы строк
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Убираем Markdown символы, если они не закрыты
    text = re.sub(r'\*\*([^*]+)$', r'\1', text)  # Незакрытый жирный
    text = re.sub(r'\*([^*]+)$', r'\1', text)  # Незакрытый курсив

    return text


def split_long_message(text: str, max_length: int = 4000) -> list:
    """Разбивает длинное сообщение на части"""
    if len(text) <= max_length:
        return [text]

    parts = []
    current_part = ""

    for line in text.split('\n'):
        if len(current_part) + len(line) + 1 > max_length:
            parts.append(current_part)
            current_part = line
        else:
            if current_part:
                current_part += '\n' + line
            else:
                current_part = line

    if current_part:
        parts.append(current_part)

    return parts