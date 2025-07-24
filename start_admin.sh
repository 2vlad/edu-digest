#!/bin/bash
set -e

# Переходим в правильную директорию
cd /Users/tovlad01/Dev/edu-digest

# Активируем виртуальное окружение
source venv/bin/activate

# Загружаем переменные окружения
export $(cat .env | xargs)

# Запускаем админ-панель
python main.py admin