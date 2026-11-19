-- SQLite schema for bank product catalog (Lab 4)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS audiences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    img_path TEXT NOT NULL,
    name TEXT NOT NULL,
    audience_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    tariff_cost INTEGER NOT NULL,
    FOREIGN KEY (audience_id) REFERENCES audiences (id)
);

CREATE INDEX IF NOT EXISTS idx_products_audience ON products (audience_id);

INSERT INTO audiences (name) VALUES
    ('Работающие'),
    ('Пенсионеры'),
    ('Студенты'),
    ('Компании'),
    ('Самозанятые');

INSERT INTO products (img_path, name, audience_id, description, tariff_cost) VALUES
    ('alfa-card.svg', 'Альфа-Карта', 1, 'Дебетовая карта с кэшбэком рублями и бесплатным обслуживанием.', 0),
    ('pension.svg', 'Пенсионная карта', 2, 'Карта для зачисления пенсии и процентов на остаток.', 0),
    ('student.svg', 'Карта для студентов', 3, 'Кэшбэк в категориях кафе, транспорт и супермаркеты.', 0),
    ('business.svg', 'Карта для бизнеса', 4, 'Карта компании для оплаты расходов сотрудников.', 590),
    ('selfemployed.svg', 'Карта самозанятого', 5, 'Разделение рабочих и личных трат, отдельный тариф.', 199),
    ('premium.svg', 'Альфа-Карта Premium', 1, 'Повышенный кэшбэк и премиальное обслуживание для работающих клиентов.', 2990);
