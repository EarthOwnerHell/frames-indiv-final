-- ==========================================
-- Сервис доставки: структура базы данных
-- ==========================================

-- Клиенты сервиса
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL
);

-- Курьеры: тип передвижения и признак занятости (0 - занят, 1 - свободен)
CREATE TABLE IF NOT EXISTS couriers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL
        CHECK (type IN ('пеший курьер', 'велокурьер', 'автокурьер')),
    is_free INTEGER NOT NULL DEFAULT 1 CHECK (is_free IN (0, 1))
);

-- Заказы: courier_id равен NULL, пока курьер не назначен;
-- created_at хранится строкой ISO 8601 (YYYY-MM-DDTHH:MM:SS)
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    courier_id INTEGER,
    distance_km REAL NOT NULL CHECK (distance_km >= 0),
    weight REAL NOT NULL CHECK (weight >= 0),
    goods_sum REAL NOT NULL CHECK (goods_sum >= 0),
    payment_is_online INTEGER NOT NULL CHECK (payment_is_online IN (0, 1)),
    created_at TEXT NOT NULL,
    is_cancelled INTEGER NOT NULL DEFAULT 0 CHECK (is_cancelled IN (0, 1)),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (courier_id) REFERENCES couriers(id)
);
