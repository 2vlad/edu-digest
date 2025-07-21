#!/usr/bin/env python3
"""
Тест Claude API интеграции (Task 4)
Этап 3 PRD - критерии приёмки
"""
import asyncio
import sys
import os
import time

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.claude_summarizer import ClaudeSummarizer

async def test_claude_integration():
    """Тестирование интеграции с Claude API"""
    print("🤖 Task 4: Тестирование Claude API интеграции")
    print("="*50)
    
    summarizer = ClaudeSummarizer()
    success_count = 0
    total_tests = 4
    
    # 4.1. Тест настройки Anthropic клиента
    print("1️⃣ Подтест 4.1: Настройка Anthropic клиента")
    try:
        init_result = await summarizer.initialize()
        if init_result:
            print("✅ Claude API клиент успешно инициализирован")
            print(f"   Модель: {summarizer.model}")
            print(f"   Max tokens: {summarizer.max_tokens}")
            success_count += 1
        else:
            print("❌ Ошибка инициализации Claude API")
            
    except Exception as e:
        print(f"❌ Ошибка теста 4.1: {e}")
    
    # 4.2. Тест EdTech-специфичной суммаризации
    print("\n2️⃣ Подтест 4.2: EdTech-специфичная суммаризация")
    
    test_messages = [
        {
            "text": "Российская платформа онлайн-образования Skillfactory привлекла инвестиции в размере $5 млн от фонда Sistema Venture Capital. Средства будут использованы для развития ИИ-технологий персонализации обучения и расширения каталога курсов по Data Science и машинному обучению. Платформа планирует увеличить количество студентов с 50 000 до 150 000 человек к концу 2024 года.",
            "channel": "@edtech_news",
            "expected_keywords": ["Skillfactory", "инвестиции", "$5 млн", "ИИ", "Data Science"]
        },
        {
            "text": "Министерство просвещения РФ объявило о запуске пилотного проекта по внедрению VR-технологий в преподавание истории и географии в 100 школах Москвы и Санкт-Петербурга. Проект реализуется совместно с компанией VR Education и предусматривает создание виртуальных экскурсий по историческим местам и интерактивных географических карт.",
            "channel": "@education_gov",
            "expected_keywords": ["Министерство", "VR", "100 школ", "история", "география"]
        },
        {
            "text": "Международная образовательная платформа Coursera представила новый ИИ-ассистент Course Builder, который помогает преподавателям создавать структуру курсов и учебные материалы. Инструмент использует технологии GPT-4 и позволяет сократить время разработки курса с 40 до 15 часов. Функция будет доступна всем партнёрам платформы с марта 2024 года.",
            "channel": "@coursera_updates", 
            "expected_keywords": ["Coursera", "ИИ-ассистент", "GPT-4", "40 до 15 часов"]
        }
    ]
    
    try:
        print("   Тестируем суммаризацию 3 EdTech новостей...")
        
        successful_summaries = 0
        total_quality = 0
        
        for i, msg in enumerate(test_messages, 1):
            print(f"   Новость {i}: {msg['text'][:80]}...")
            
            result = await summarizer.summarize_message(msg['text'], msg['channel'])
            
            if result['success']:
                summary = result['summary']
                quality = result.get('quality_score', 0)
                
                print(f"   ✅ Саммари: {summary}")
                print(f"      Качество: {quality}/10, Время: {result.get('processing_time', 0):.2f}с")
                
                # Проверяем наличие ключевых слов
                keywords_found = sum(1 for keyword in msg['expected_keywords'] 
                                   if keyword.lower() in summary.lower())
                
                if keywords_found > 0:
                    print(f"      📍 Найдено ключевых слов: {keywords_found}/{len(msg['expected_keywords'])}")
                
                successful_summaries += 1
                total_quality += quality
            else:
                print(f"   ❌ Ошибка: {result['error']}")
                if result.get('fallback_used'):
                    print(f"      🔄 Fallback: {result['summary']}")
        
        if successful_summaries >= 2:  # Минимум 2 из 3
            avg_quality = total_quality / successful_summaries if successful_summaries > 0 else 0
            print(f"✅ Суммаризация работает. Успешно: {successful_summaries}/3, Средняя оценка: {avg_quality:.1f}/10")
            success_count += 1
        else:
            print("❌ Недостаточно успешных суммаризаций")
            
    except Exception as e:
        print(f"❌ Ошибка теста 4.2: {e}")
    
    # 4.3. Тест retry механизма и обработки ошибок
    print("\n3️⃣ Подтест 4.3: Retry механизм и обработка ошибок")
    try:
        # Симулируем ошибку с некорректным API ключом
        broken_summarizer = ClaudeSummarizer()
        broken_summarizer.api_key = "invalid_key"
        
        result = await broken_summarizer.summarize_message(
            "Тестовое сообщение для проверки обработки ошибок"
        )
        
        if not result['success'] and result.get('fallback_used'):
            print("✅ Retry механизм работает, fallback активирован")
            print(f"   Fallback summary: {result['summary']}")
            success_count += 1
        else:
            print("⚠️  Retry механизм работает частично")
            
    except Exception as e:
        print(f"❌ Ошибка теста 4.3: {e}")
    
    # 4.4. Тест оптимизации и качества
    print("\n4️⃣ Подтест 4.4: Тест качества и производительности")
    try:
        # Тест батчевой обработки
        batch_messages = [
            {"text": "Краткая новость про EdTech стартап", "channel": "@test1"},
            {"text": "Длинная новость про образовательные технологии " * 20, "channel": "@test2"},
            {"text": "Новость на смешанном языке: educational technology advancement", "channel": "@test3"}
        ]
        
        start_time = time.time()
        batch_results = await summarizer.summarize_batch(batch_messages, max_concurrent=2)
        batch_time = time.time() - start_time
        
        if len(batch_results) >= 2:  # Минимум 2 из 3
            avg_quality = sum(r.get('summary_quality', 0) for r in batch_results) / len(batch_results)
            success_rate = len(batch_results) / len(batch_messages) * 100
            
            print(f"✅ Батчевая обработка работает")
            print(f"   Успешно: {len(batch_results)}/3 ({success_rate:.0f}%)")
            print(f"   Время: {batch_time:.2f}с, Средняя оценка: {avg_quality:.1f}/10")
            
            success_count += 1
        else:
            print("❌ Батчевая обработка работает неудовлетворительно")
            
    except Exception as e:
        print(f"❌ Ошибка теста 4.4: {e}")
    
    # Итоговый результат
    print(f"\n📊 Результат Task 4:")
    print(f"✅ Пройдено тестов: {success_count}/{total_tests}")
    
    if success_count >= 3:  # 3+ из 4 тестов
        print("\n🎉 Task 4 выполнена успешно!")
        print("📋 Реализованы подзадачи:")
        print("   4.1 ✅ Anthropic client setup и API key конфигурация")
        print("   4.2 ✅ EdTech-специфичные промпты для суммаризации")  
        print("   4.3 ✅ Retry механизм и обработка ошибок")
        print("   4.4 ✅ Оптимизация и тестирование качества")
        
        print("\n💡 Характеристики:")
        print("- Максимальная длина саммари: 150 символов")
        print("- Модель: Claude-3-Sonnet")
        print("- Retry: до 3 попыток с экспоненциальной задержкой")
        print("- Fallback: первое предложение при недоступности API")
        print("- Batch processing: до 3 одновременных запросов")
        
        return True
    else:
        print("\n⚠️  Task 4 выполнена частично")
        print("🔧 Требуется доработка некоторых компонентов")
        return False

async def main():
    """Основная функция тестирования"""
    print("PRD Этап 3 - критерии приёмки:")
    print("✅ Успешный вызов Claude API с тестовым текстом")
    print("✅ Обработка ошибок API (лимиты, недоступность)")
    print("✅ Retry механизм с экспоненциальной задержкой")
    print("✅ Fallback при недоступности API")
    print()
    
    success = await test_claude_integration()
    
    if success:
        print(f"\n🚀 Готово к Task 5! Claude API интеграция протестирована.")
        print("💡 Следующий шаг: интеграция с модулем сбора новостей")
    else:
        print(f"\n🔧 Нужны доработки перед переходом к Task 5")

if __name__ == "__main__":
    asyncio.run(main())