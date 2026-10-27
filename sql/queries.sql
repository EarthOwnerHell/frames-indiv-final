-- ==========================================
-- Сервис доставки: SQL-запросы проекта
-- ==========================================
-- Статус заказа вычисляется так же, как свойство Order.status:
--   is_cancelled = 1        -> 'отменён'
--   courier_id IS NULL      -> 'ожидает курьера'
--   иначе                   -> 'передан курьеру'
-- Значения, которые в Django приходят от пользователя или из URL,
-- передаются параметрами (?). Здесь для проверки в SQLite CLI
-- подставлены примеры значений.


-- ------------------------------------------
-- Выборка списков
-- ------------------------------------------

-- 1. Список всех курьеров по имени (страница /couriers/)
SELECT
    id,
    name,
    type,
    is_free
FROM couriers
ORDER BY name;

-- 2. Три последних заказа (главная страница /)
SELECT
    id,
    strftime('%d.%m.%Y %H:%M', created_at) AS created_at_display,
    goods_sum,
    CASE
        WHEN is_cancelled = 1 THEN 'отменён'
        WHEN courier_id IS NULL THEN 'ожидает курьера'
        ELSE 'передан курьеру'
    END AS status
FROM orders
ORDER BY created_at DESC
LIMIT 3;


-- ------------------------------------------
-- Фильтрация (WHERE)
-- ------------------------------------------

-- 3. Курьер по идентификатору (страница /couriers/<id>/, параметр id)
SELECT
    id,
    name,
    type,
    is_free
FROM couriers
WHERE id = 2;

-- 4. Свободные курьеры нужного типа (страница /couriers/available/;
--    тип определяется по весу заказа функцией courier_type())
SELECT
    id,
    name,
    type
FROM couriers
WHERE type = 'пеший курьер'
  AND is_free = 1
ORDER BY name;


-- ------------------------------------------
-- Соединение таблиц (JOIN)
-- ------------------------------------------

-- 5. Список заказов с именами клиента и курьера (страница /orders/).
--    LEFT JOIN: заказ без курьера тоже попадает в список
SELECT
    orders.id,
    strftime('%d.%m.%Y %H:%M', orders.created_at) AS created_at_display,
    customers.name AS customer_name,
    couriers.name AS courier_name,
    orders.goods_sum,
    CASE
        WHEN orders.is_cancelled = 1 THEN 'отменён'
        WHEN orders.courier_id IS NULL THEN 'ожидает курьера'
        ELSE 'передан курьеру'
    END AS status
FROM orders
JOIN customers
    ON orders.customer_id = customers.id
LEFT JOIN couriers
    ON orders.courier_id = couriers.id
ORDER BY orders.created_at DESC;

-- 6. Полная информация о заказе (страница /orders/<id>/, параметр id)
SELECT
    orders.id,
    orders.distance_km,
    orders.weight,
    orders.goods_sum,
    orders.payment_is_online,
    orders.created_at,
    orders.is_cancelled,
    customers.id AS customer_id,
    customers.name AS customer_name,
    customers.phone AS customer_phone,
    couriers.id AS courier_id,
    couriers.name AS courier_name,
    couriers.type AS courier_type,
    couriers.is_free AS courier_is_free
FROM orders
JOIN customers
    ON orders.customer_id = customers.id
LEFT JOIN couriers
    ON orders.courier_id = couriers.id
WHERE orders.id = 1047;

-- 7. Заказы конкретного курьера (страница /couriers/<id>/, параметр id)
SELECT
    orders.id,
    customers.name AS customer_name,
    CASE
        WHEN orders.is_cancelled = 1 THEN 'отменён'
        WHEN orders.courier_id IS NULL THEN 'ожидает курьера'
        ELSE 'передан курьеру'
    END AS status
FROM orders
JOIN customers
    ON orders.customer_id = customers.id
WHERE orders.courier_id = 1
ORDER BY orders.created_at DESC;

-- 8. Активные заказы, ожидающие курьера (страница /orders/statistics/)
SELECT
    orders.id,
    strftime('%d.%m.%Y %H:%M', orders.created_at) AS created_at_display,
    customers.name AS customer_name,
    orders.weight
FROM orders
JOIN customers
    ON orders.customer_id = customers.id
WHERE orders.courier_id IS NULL
  AND orders.is_cancelled = 0
ORDER BY orders.created_at;


-- ------------------------------------------
-- Агрегатные функции
-- ------------------------------------------

-- 9. Сводка по активным заказам: количество, сумма и средний чек
--    товаров (страница /orders/statistics/)
SELECT
    COUNT(*) AS orders_count,
    ROUND(SUM(goods_sum), 2) AS goods_total,
    ROUND(AVG(goods_sum), 2) AS goods_avg
FROM orders
WHERE is_cancelled = 0;

-- 10. Сводка по курьерам: всего и свободных (главная страница /)
SELECT
    COUNT(*) AS couriers_count,
    SUM(is_free) AS free_count
FROM couriers;


-- ------------------------------------------
-- Группировка (GROUP BY) и фильтрация групп (HAVING)
-- ------------------------------------------

-- 11. Количество заказов по статусам (страница /orders/statistics/)
SELECT
    CASE
        WHEN is_cancelled = 1 THEN 'отменён'
        WHEN courier_id IS NULL THEN 'ожидает курьера'
        ELSE 'передан курьеру'
    END AS status,
    COUNT(*) AS orders_count
FROM orders
GROUP BY status
ORDER BY orders_count DESC;

-- 12. Нагрузка курьеров: всего заказов и активных.
--     LEFT JOIN оставляет курьеров без заказов (с нулём),
--     COUNT(CASE ...) считает только активные заказы
SELECT
    couriers.id,
    couriers.name,
    couriers.type,
    COUNT(orders.id) AS orders_count,
    COUNT(CASE WHEN orders.is_cancelled = 0 THEN 1 END) AS active_count
FROM couriers
LEFT JOIN orders
    ON couriers.id = orders.courier_id
GROUP BY couriers.id, couriers.name, couriers.type
ORDER BY orders_count DESC, couriers.name;

-- 13. Активные заказы и сумма товаров по клиентам
--     (страница /orders/statistics/)
SELECT
    customers.name AS customer_name,
    COUNT(orders.id) AS orders_count,
    ROUND(COALESCE(SUM(orders.goods_sum), 0), 2) AS goods_total
FROM customers
LEFT JOIN orders
    ON customers.id = orders.customer_id
    AND orders.is_cancelled = 0
GROUP BY customers.id, customers.name
ORDER BY goods_total DESC;

-- 14. Постоянные клиенты: больше одного активного заказа
--     (страница /orders/statistics/, порог передаётся параметром)
SELECT
    customers.name AS customer_name,
    COUNT(orders.id) AS orders_count
FROM customers
JOIN orders
    ON customers.id = orders.customer_id
WHERE orders.is_cancelled = 0
GROUP BY customers.id, customers.name
HAVING COUNT(orders.id) > 1
ORDER BY orders_count DESC;
