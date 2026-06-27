-- Инициализация схемы БД AirSeek
-- Запускается автоматически при первом старте PostgreSQL контейнера

CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- для gen_random_uuid()

-- ============================================================
-- STATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS stations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    latitude    NUMERIC(10, 8) NOT NULL,
    longitude   NUMERIC(11, 8) NOT NULL,
    district    VARCHAR(100),
    source      VARCHAR(50)  NOT NULL,
    external_id VARCHAR(255),
    is_active   BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMPTZ  DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stations_location
    ON stations (latitude, longitude);

CREATE INDEX IF NOT EXISTS idx_stations_active
    ON stations (is_active);

CREATE UNIQUE INDEX IF NOT EXISTS idx_stations_source_external
    ON stations (source, external_id)
    WHERE external_id IS NOT NULL;

-- ============================================================
-- MEASUREMENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS measurements (
    id           BIGSERIAL PRIMARY KEY,
    station_id   UUID        NOT NULL REFERENCES stations(id),
    measured_at  TIMESTAMPTZ NOT NULL,
    aqi          INTEGER,
    pm25         NUMERIC(7, 2),
    pm10         NUMERIC(7, 2),
    co           NUMERIC(7, 2),
    no2          NUMERIC(7, 2),
    so2          NUMERIC(7, 2),
    o3           NUMERIC(7, 2),
    temperature  NUMERIC(5, 2),
    humidity     NUMERIC(5, 2),
    source_raw   JSONB,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_measurements_station_time
    ON measurements (station_id, measured_at DESC);

CREATE INDEX IF NOT EXISTS idx_measurements_time
    ON measurements (measured_at DESC);

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name          VARCHAR(255),
    fcm_token     VARCHAR(512),
    is_active     BOOLEAN     DEFAULT TRUE,
    is_verified   BOOLEAN     DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- USER_SUBSCRIPTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    station_id    UUID NOT NULL REFERENCES stations(id) ON DELETE CASCADE,
    aqi_threshold INTEGER     DEFAULT 100,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, station_id)
);

-- ============================================================
-- NOTIFICATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    station_id  UUID        REFERENCES stations(id),
    type        VARCHAR(50) NOT NULL,
    title       VARCHAR(255) NOT NULL,
    body        TEXT        NOT NULL,
    aqi_value   INTEGER,
    is_sent     BOOLEAN     DEFAULT FALSE,
    sent_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user
    ON notifications (user_id, created_at DESC);

-- ============================================================
-- AI_PREDICTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS ai_predictions (
    id              BIGSERIAL PRIMARY KEY,
    station_id      UUID        NOT NULL REFERENCES stations(id),
    model_name      VARCHAR(100) NOT NULL,
    model_version   VARCHAR(50),
    prediction_type VARCHAR(50) NOT NULL,
    predicted_at    TIMESTAMPTZ NOT NULL,
    predicted_aqi   INTEGER,
    confidence      NUMERIC(4, 3),
    summary         TEXT,
    recommendations TEXT,
    raw_response    JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_station_time
    ON ai_predictions (station_id, predicted_at DESC);
