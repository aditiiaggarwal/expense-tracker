-- Users table
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    shop_name     TEXT NOT NULL,
    owner_name    TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password      TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock table
CREATE TABLE IF NOT EXISTS stock (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER REFERENCES users(id),
    item_name     TEXT NOT NULL,
    quantity      INTEGER NOT NULL DEFAULT 0,
    unit          TEXT,
    low_stock_alert INTEGER DEFAULT 5,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bills table
CREATE TABLE IF NOT EXISTS bills (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER REFERENCES users(id),
    customer_name TEXT,
    total_amount  REAL NOT NULL,
    status        TEXT DEFAULT 'paid',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bill items table
CREATE TABLE IF NOT EXISTS bill_items (
    id            SERIAL PRIMARY KEY,
    bill_id       INTEGER REFERENCES bills(id),
    item_name     TEXT NOT NULL,
    quantity      INTEGER NOT NULL,
    price         REAL NOT NULL
);