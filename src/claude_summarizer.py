import asyncio
import logging
import time
from typing import List, Dict, Optional, Any
from datetime import datetime

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from .config import ANTHROPIC_API_KEY
from .database import SettingsDB

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/claude.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ClaudeSummarizer:
    """Класс для суммаризации новостей через Claude API"""
    
    def __init__(self):
        """4.1. Anthropic client setup и API key конфигурация"""
        self.client = None
        self.initialized = False
        self.api_key = ANTHROPIC_API_KEY
        self.model = "claude-3-sonnet-20240229"  # Используем Sonnet для качества
        
        # Настройки по умолчанию
        self.max_tokens = 150
        self.temperature = 0.1  # Низкая температура для консистентности
        
    async def initialize(self):
        """Инициализация Claude клиента"""
        try:
            if not self.api_key or self.api_key == "your_claude_api_key":
                raise ValueError("ANTHROPIC_API_KEY не настроен в .env")
            
            self.client = AsyncAnthropic(
            api_key=self.api_key,
            max_retries=0  # Мы сами управляем retry логикой
        )
            
            # Получаем настройки из базы данных
            max_length = SettingsDB.get_setting('summary_max_length', '150')
            self.max_tokens = int(max_length)
            
            self.initialized = True
            logger.info("Claude API клиент успешно инициализирован")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Claude API: {e}")
            return False
    
    def _get_edtech_prompt(self, message_text: str, channel_name: str = "") -> tuple[str, List[MessageParam]]:
        """4.2. EdTech-специфичные промпты для суммаризации"""
        
        # Базовый системный промпт для образовательных технологий
        system_prompt = """Ты - эксперт по образовательным технологиям (EdTech). 
Твоя задача - создавать краткие, информативные саммари новостей из EdTech индустрии.

ПРАВИЛА СУММАРИЗАЦИИ:
1. Максимум 1-2 предложения (до 150 символов)
2. Фокус на ключевой информации: что произошло, кто участвует, какой результат
3. Используй профессиональную терминологию EdTech
4. Избегай воды и общих фраз
5. Если упоминаются суммы инвестиций, технологии или ключевые метрики - включай их
6. Пиши на русском языке

ПРИМЕРЫ ХОРОШИХ САММАРИ:
"Стартап AI-тьютор Synthesis привлек $15M Series A для персонализации обучения математике"
"Coursera запустила ИИ-ассистента для создания курсов, сокращающего время разработки на 60%"
"Министерство образования РФ внедряет VR-технологии в 1000 школ к 2025 году"

ИЗБЕГАЙ:
- Общих фраз типа "интересная новость", "важное событие"
- Пересказа без выводов
- Слишком технических деталей
- Эмоциональных оценок"""

        user_prompt = f"""Создай краткое саммари для этой новости из EdTech:

ТЕКСТ НОВОСТИ:
{message_text}

КАНАЛ: {channel_name}

Напиши саммари в одно предложение, максимум 150 символов, сфокусировавшись на главном факте или результате."""

        messages = [{"role": "user", "content": user_prompt}]
        
        return system_prompt, messages
    
    async def summarize_message(self, message_text: str, channel_name: str = "", 
                               retry_count: int = 0) -> Dict[str, Any]:
        """Суммаризация одного сообщения с обработкой ошибок"""
        
        if not self.initialized:
            await self.initialize()
        
        if not self.initialized:
            return {
                "success": False,
                "error": "Claude API не инициализирован",
                "summary": message_text[:100] + "...",  # Fallback
                "fallback_used": True
            }
        
        try:
            # Подготавливаем промпт
            system_prompt, messages = self._get_edtech_prompt(message_text, channel_name)
            
            # Отправляем запрос к Claude API
            start_time = time.time()
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages
            )
            
            processing_time = time.time() - start_time
            
            # Извлекаем текст суммаризации
            if response.content and len(response.content) > 0:
                summary = response.content[0].text.strip()
                
                # Проверяем качество суммаризации
                quality_check = self._validate_summary_quality(summary, message_text)
                
                logger.info(f"Суммаризация выполнена за {processing_time:.2f}с. Качество: {quality_check['score']}/10")
                
                return {
                    "success": True,
                    "summary": summary,
                    "processing_time": processing_time,
                    "quality_score": quality_check['score'],
                    "quality_issues": quality_check['issues'],
                    "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                    "fallback_used": False
                }
            else:
                raise Exception("Пустой ответ от Claude API")
                
        except Exception as e:
            logger.error(f"Ошибка суммаризации (попытка {retry_count + 1}): {e}")
            
            # 4.3. Retry механизм и обработка ошибок
            if retry_count < 3:  # Максимум 3 попытки
                await asyncio.sleep(2 ** retry_count)  # Экспоненциальная задержка
                return await self.summarize_message(message_text, channel_name, retry_count + 1)
            
            # 4.4. Fallback при недоступности
            fallback_summary = self._create_fallback_summary(message_text)
            
            return {
                "success": False,
                "error": str(e),
                "summary": fallback_summary,
                "fallback_used": True,
                "retry_count": retry_count
            }
    
    def _validate_summary_quality(self, summary: str, original_text: str) -> Dict[str, Any]:
        """4.4. Оптимизация и тестирование качества суммаризации"""
        issues = []
        score = 10  # Начинаем с максимума
        
        # Проверка длины
        if len(summary) > 150:
            issues.append("Превышена максимальная длина")
            score -= 2
        
        if len(summary) < 20:
            issues.append("Слишком короткое саммари")
            score -= 1
        
        # Проверка содержания
        if not summary.strip():
            issues.append("Пустое саммари")
            score -= 5
        
        # Проверка на общие фразы
        generic_phrases = ["интересная новость", "важное событие", "стоит отметить"]
        if any(phrase in summary.lower() for phrase in generic_phrases):
            issues.append("Содержит общие фразы")
            score -= 1
        
        # Проверка на русский язык
        cyrillic_count = sum(1 for char in summary if 'а' <= char.lower() <= 'я')
        if cyrillic_count < len(summary) * 0.5:
            issues.append("Мало русских символов")
            score -= 1
        
        # Проверка на наличие ключевых EdTech терминов (бонус)
        edtech_terms = ['стартап', 'инвестиции', 'платформа', 'курс', 'обучение', 
                       'образование', 'технологии', 'ИИ', 'AI', 'VR', 'AR']
        if any(term.lower() in summary.lower() for term in edtech_terms):
            score = min(10, score + 1)  # Бонус за релевантность
        
        return {
            "score": max(0, score),
            "issues": issues
        }
    
    def _create_fallback_summary(self, message_text: str) -> str:
        """Создание резервного саммари при недоступности Claude"""
        # Простая логика: берем первое предложение или первые 100 символов
        text = message_text.strip()
        
        # Пытаемся найти первое предложение
        sentences = text.split('.')
        if sentences and len(sentences[0]) <= 120:
            return sentences[0].strip() + "."
        
        # Если не получилось, берем первые 100 символов
        return (text[:100] + "...") if len(text) > 100 else text
    
    async def summarize_batch(self, messages: List[Dict], max_concurrent: int = 3) -> List[Dict]:
        """Батчевая суммаризация с контролем нагрузки"""
        if not messages:
            return []
        
        logger.info(f"Начинаем батчевую суммаризацию {len(messages)} сообщений")
        
        # Создаем семафор для ограничения одновременных запросов
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def summarize_one(message_data):
            async with semaphore:
                result = await self.summarize_message(
                    message_data['text'],
                    message_data.get('channel', '')
                )
                
                return {
                    **message_data,
                    'summary': result['summary'],
                    'summary_success': result['success'],
                    'summary_quality': result.get('quality_score', 0),
                    'processing_time': result.get('processing_time', 0),
                    'fallback_used': result.get('fallback_used', False)
                }
        
        # Запускаем все задачи параллельно
        tasks = [summarize_one(msg) for msg in messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        successful_summaries = []
        failed_summaries = []
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Ошибка в batch суммаризации: {result}")
                failed_summaries.append(result)
            else:
                successful_summaries.append(result)
        
        success_rate = len(successful_summaries) / len(messages) * 100
        avg_quality = sum(r.get('summary_quality', 0) for r in successful_summaries) / len(successful_summaries) if successful_summaries else 0
        
        logger.info(f"Батч завершен. Успешно: {len(successful_summaries)}/{len(messages)} ({success_rate:.1f}%). Средняя оценка качества: {avg_quality:.1f}/10")
        
        return successful_summaries
    
    async def test_api_connection(self) -> Dict[str, Any]:
        """Тестирование подключения к Claude API"""
        try:
            if not self.initialized:
                await self.initialize()
            
            if not self.initialized:
                return {"status": "error", "message": "Не удалось инициализировать API"}
            
            # Тестовый запрос
            test_text = "Компания OpenAI представила новую модель GPT-4 Turbo с улучшенными возможностями для образовательных приложений. Модель показала на 40% лучшие результаты в задачах по созданию персонализированного обучающего контента."
            
            result = await self.summarize_message(test_text, "@test_channel")
            
            if result['success']:
                return {
                    "status": "success", 
                    "test_summary": result['summary'],
                    "quality_score": result.get('quality_score', 0),
                    "processing_time": result.get('processing_time', 0),
                    "model": self.model,
                    "max_tokens": self.max_tokens
                }
            else:
                return {
                    "status": "error", 
                    "message": result['error'],
                    "fallback_used": result.get('fallback_used', False)
                }
        
        except Exception as e:
            logger.error(f"Ошибка тестирования Claude API: {e}")
            return {"status": "error", "message": str(e)}

# Глобальный экземпляр суммаризатора
_summarizer_instance = None

async def get_claude_summarizer() -> ClaudeSummarizer:
    """Получение инициализированного экземпляра суммаризатора"""
    global _summarizer_instance
    if _summarizer_instance is None:
        _summarizer_instance = ClaudeSummarizer()
        await _summarizer_instance.initialize()
    return _summarizer_instance