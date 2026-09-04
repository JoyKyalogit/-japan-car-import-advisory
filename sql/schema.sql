-- Japan Car Import Advisory Platform schema

CREATE TABLE IF NOT EXISTS car_listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_platform VARCHAR(50) NOT NULL,
    listing_id VARCHAR(100),
    title VARCHAR(300),
    make VARCHAR(80),
    model VARCHAR(120),
    year INTEGER,
    mileage_km INTEGER,
    engine_cc INTEGER,
    fuel_type VARCHAR(30),
    transmission VARCHAR(30),
    body_type VARCHAR(50),
    price_jpy REAL,
    price_usd REAL,
    currency VARCHAR(10) DEFAULT 'JPY',
    location VARCHAR(100),
    listing_url TEXT,
    image_url TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_cleaned INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_listings_platform ON car_listings(source_platform);
CREATE INDEX IF NOT EXISTS idx_listings_make_model ON car_listings(make, model);
CREATE INDEX IF NOT EXISTS idx_listings_year ON car_listings(year);

CREATE TABLE IF NOT EXISTS local_market_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make VARCHAR(80),
    model VARCHAR(120),
    year INTEGER,
    avg_price_kes REAL,
    min_price_kes REAL,
    max_price_kes REAL,
    source VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS import_cost_estimates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    car_listing_id INTEGER,
    purchase_price_usd REAL,
    shipping_usd REAL,
    insurance_usd REAL,
    cif_usd REAL,
    import_duty_kes REAL,
    excise_duty_kes REAL,
    vat_kes REAL,
    rdl_kes REAL,
    idf_kes REAL,
    port_charges_kes REAL,
    clearing_fees_kes REAL,
    registration_kes REAL,
    other_charges_kes REAL,
    total_import_kes REAL,
    local_market_kes REAL,
    potential_savings_kes REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
