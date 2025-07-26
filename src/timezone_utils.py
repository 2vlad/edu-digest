#!/usr/bin/env python3
"""
Утилиты для работы с московским временем
Все времена в системе приводятся к московскому времени (UTC+3)
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

# Московский часовой пояс (UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))

def now_moscow() -> datetime:
    """Текущее время в Москве"""
    return datetime.now(MOSCOW_TZ)

def utc_to_moscow(dt: datetime) -> datetime:
    """Конвертация UTC в московское время"""
    if dt.tzinfo is None:
        # Если нет timezone, считаем что это UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MOSCOW_TZ)

def moscow_to_utc(dt: datetime) -> datetime:
    """Конвертация московского времени в UTC"""
    if dt.tzinfo is None:
        # Если нет timezone, считаем что это московское время
        dt = dt.replace(tzinfo=MOSCOW_TZ)
    return dt.astimezone(timezone.utc)

def parse_moscow_time(time_str: str, date_obj: Optional[datetime] = None) -> datetime:
    """
    Парсинг времени как московского
    time_str: "12:00" 
    date_obj: дата (по умолчанию сегодня по Москве)
    """
    if date_obj is None:
        date_obj = now_moscow().date()
    
    hour, minute = map(int, time_str.split(':'))
    moscow_dt = datetime.combine(date_obj, datetime.min.time().replace(hour=hour, minute=minute))
    return moscow_dt.replace(tzinfo=MOSCOW_TZ)

def format_moscow_time(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S MSK") -> str:
    """Форматирование времени в московском часовом поясе"""
    moscow_dt = utc_to_moscow(dt) if dt.tzinfo == timezone.utc else dt
    if moscow_dt.tzinfo != MOSCOW_TZ:
        moscow_dt = moscow_dt.astimezone(MOSCOW_TZ)
    return moscow_dt.strftime(format_str)

def get_moscow_schedule_times() -> list:
    """Получение времен расписания в московском времени"""
    try:
        from .database import SettingsDB
        digest_times = SettingsDB.get_setting('digest_times', '12:00,18:00')
        times = [t.strip() for t in digest_times.split(',') if t.strip()]
        return times
    except Exception:
        return ['12:00', '18:00']

def is_moscow_time_in_range(current_time: datetime, start_hour: int, end_hour: int) -> bool:
    """Проверка попадания московского времени в диапазон часов"""
    moscow_time = utc_to_moscow(current_time) if current_time.tzinfo == timezone.utc else current_time
    hour = moscow_time.hour
    return start_hour <= hour < end_hour

def get_digest_type_by_moscow_time(dt: Optional[datetime] = None) -> str:
    """Определение типа дайджеста по московскому времени"""
    if dt is None:
        dt = now_moscow()
    else:
        dt = utc_to_moscow(dt) if dt.tzinfo == timezone.utc else dt
    
    hour = dt.hour
    
    if 0 <= hour <= 12:
        return "Утренний"
    elif 13 <= hour <= 17:
        return "Дневной"
    else:
        return "Вечерний"

def moscow_hours_ago(hours: int) -> datetime:
    """Московское время N часов назад в UTC для сравнения"""
    moscow_now = now_moscow()
    moscow_past = moscow_now - timedelta(hours=hours)
    return moscow_to_utc(moscow_past)