#!/usr/bin/env python3
"""
Тест для проверки логики заголовков дайджестов
"""

from datetime import datetime, timezone, timedelta, time

def get_digest_title(test_time_str: str) -> str:
    """
    Тестирует генерацию заголовка для заданного времени
    test_time_str в формате "HH:MM"
    """
    # Парсим время
    hour, minute = map(int, test_time_str.split(':'))
    
    # Создаем тестовую дату (используем сегодня)
    today = datetime.now().date()
    test_datetime = datetime.combine(today, time(hour, minute))
    
    current_time = test_datetime.time()
    current_date = test_datetime.date()
    
    # Определяем тип дайджеста по времени (как в основном коде)
    if time(0, 0) <= current_time <= time(12, 29):
        # С 00:00 до 12:29 - утренний дайджест текущего дня
        digest_type = "Утренний"
        digest_date = current_date
    elif time(12, 30) <= current_time <= time(17, 30):
        # С 12:30 до 17:30 - дневной дайджест
        digest_type = "Дневной" 
        digest_date = current_date
    else:
        # С 17:31 до 23:59 - вечерний дайджест
        digest_type = "Вечерний"
        digest_date = current_date
    
    # Форматируем дату по-русски
    months_ru = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа", 
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    
    date_str = f"{digest_date.day} {months_ru[digest_date.month]}"
    digest_title = f"{digest_type} дайджест {date_str}"
    
    return digest_title

def main():
    """Тестируем различные времена"""
    test_times = [
        "00:00",  # Утренний
        "06:30",  # Утренний
        "12:29",  # Утренний (граница)
        "12:30",  # Дневной (граница)
        "14:00",  # Дневной
        "17:30",  # Дневной (граница)
        "17:31",  # Вечерний (граница)
        "20:00",  # Вечерний
        "23:59"   # Вечерний
    ]
    
    print("🧪 Тестирование заголовков дайджестов")
    print("=" * 50)
    
    for test_time in test_times:
        title = get_digest_title(test_time)
        print(f"{test_time:>5} МСК → {title}")
    
    print("=" * 50)
    print("✅ Тест завершен!")

if __name__ == "__main__":
    main()