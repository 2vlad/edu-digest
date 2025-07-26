-- SQL для создания таблицы pending_news в Supabase
-- Выполните этот SQL в Supabase SQL Editor

CREATE TABLE IF NOT EXISTS pending_news (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    message_id BIGINT NOT NULL,
    channel_name TEXT NOT NULL,
    message_text TEXT NOT NULL,
    summary TEXT NOT NULL,
    relevance_score INTEGER DEFAULT 5,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scheduled_for DATE,
    digest_type VARCHAR(20),
    is_approved BOOLEAN DEFAULT true,
    is_deleted BOOLEAN DEFAULT false,
    UNIQUE(channel_id, message_id)
);

-- Создаем индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_pending_news_scheduled_for ON pending_news(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_pending_news_digest_type ON pending_news(digest_type);
CREATE INDEX IF NOT EXISTS idx_pending_news_is_deleted ON pending_news(is_deleted);
CREATE INDEX IF NOT EXISTS idx_pending_news_relevance_score ON pending_news(relevance_score);

-- Проверяем что таблица создалась
SELECT COUNT(*) as table_exists FROM information_schema.tables 
WHERE table_name = 'pending_news' AND table_schema = 'public';