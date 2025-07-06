-- Migration 001: Initial Database Schema
-- Translation Cost Calculator - Initial database setup
-- Version: 1.0
-- Applied: 2025-01-04
-- Description: Creates all core tables, indexes, views, and initial data

-- This migration creates the complete database structure for the Translation Cost Calculator
-- including all tables, relationships, constraints, indexes, views, and triggers.

-- =============================================================================
-- ENABLE CONSTRAINTS
-- =============================================================================

PRAGMA foreign_keys = ON;

-- =============================================================================
-- CORE ENTITY TABLES
-- =============================================================================

-- Translators table
CREATE TABLE translators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    company TEXT,
    tax_id TEXT,
    payment_terms TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    
    CONSTRAINT ck_translator_name_length CHECK (LENGTH(TRIM(name)) >= 2),
    CONSTRAINT ck_translator_email_format CHECK (
        email IS NULL OR 
        (email LIKE '%@%.%' AND LENGTH(email) >= 5)
    ),
    UNIQUE(name)
);

-- Clients table
CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    company_registration TEXT,
    tax_id TEXT,
    payment_terms TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    
    CONSTRAINT ck_client_name_length CHECK (LENGTH(TRIM(name)) >= 2),
    CONSTRAINT ck_client_email_format CHECK (
        email IS NULL OR 
        (email LIKE '%@%.%' AND LENGTH(email) >= 5)
    ),
    UNIQUE(name)
);

-- Language pairs table
CREATE TABLE language_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_language TEXT NOT NULL,
    target_language TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT ck_language_codes_valid CHECK (
        LENGTH(TRIM(source_language)) >= 2 AND
        LENGTH(TRIM(target_language)) >= 2 AND
        TRIM(source_language) != TRIM(target_language)
    ),
    UNIQUE(source_language, target_language)
);

-- Match categories table
CREATE TABLE match_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT ck_category_name_length CHECK (LENGTH(TRIM(name)) >= 1),
    CONSTRAINT ck_display_order_positive CHECK (display_order > 0)
);

-- =============================================================================
-- RATE SYSTEM TABLES
-- =============================================================================

-- Translator rates table
CREATE TABLE translator_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    translator_id INTEGER NOT NULL,
    client_id INTEGER NULL,
    language_pair_id INTEGER NOT NULL,
    match_category_id INTEGER NOT NULL,
    rate_per_word DECIMAL(10,4) NOT NULL DEFAULT 0.0000,
    minimum_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    is_minimum_fee_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    currency TEXT NOT NULL DEFAULT 'EUR',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    
    FOREIGN KEY (translator_id) REFERENCES translators(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (language_pair_id) REFERENCES language_pairs(id) ON DELETE RESTRICT,
    FOREIGN KEY (match_category_id) REFERENCES match_categories(id) ON DELETE RESTRICT,
    
    CONSTRAINT ck_rate_positive CHECK (rate_per_word >= 0.0000),
    CONSTRAINT ck_minimum_fee_positive CHECK (minimum_fee >= 0.00),
    CONSTRAINT ck_currency_code CHECK (LENGTH(TRIM(currency)) = 3),
    
    UNIQUE(translator_id, client_id, language_pair_id, match_category_id)
);

-- =============================================================================
-- PROJECT SYSTEM TABLES
-- =============================================================================

-- Projects table
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    translator_id INTEGER NOT NULL,
    client_id INTEGER NULL,
    language_pair_id INTEGER NOT NULL,
    mt_percentage INTEGER NOT NULL DEFAULT 70,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    
    FOREIGN KEY (translator_id) REFERENCES translators(id) ON DELETE RESTRICT,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL,
    FOREIGN KEY (language_pair_id) REFERENCES language_pairs(id) ON DELETE RESTRICT,
    
    CONSTRAINT ck_project_name_length CHECK (LENGTH(TRIM(name)) >= 1),
    CONSTRAINT ck_mt_percentage_range CHECK (mt_percentage >= 0 AND mt_percentage <= 100)
);

-- Project files table
CREATE TABLE project_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    parsed_data TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    file_hash TEXT,
    cat_tool TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    
    CONSTRAINT ck_filename_length CHECK (LENGTH(TRIM(filename)) >= 1),
    CONSTRAINT ck_file_path_length CHECK (LENGTH(TRIM(file_path)) >= 1),
    CONSTRAINT ck_parsed_data_not_empty CHECK (LENGTH(TRIM(parsed_data)) >= 1),
    CONSTRAINT ck_file_size_positive CHECK (file_size >= 0)
);

-- =============================================================================
-- SYSTEM TABLES
-- =============================================================================

-- Application settings table
CREATE TABLE app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    setting_type TEXT NOT NULL DEFAULT 'string',
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    
    CONSTRAINT ck_setting_key_length CHECK (LENGTH(TRIM(setting_key)) >= 1),
    CONSTRAINT ck_setting_type_valid CHECK (
        setting_type IN ('string', 'integer', 'boolean', 'decimal', 'json')
    )
);

-- =============================================================================
-- PERFORMANCE INDEXES
-- =============================================================================

-- Translator indexes
CREATE INDEX idx_translators_name ON translators(name);
CREATE INDEX idx_translators_active ON translators(is_active);
CREATE INDEX idx_translators_email ON translators(email) WHERE email IS NOT NULL;

-- Client indexes
CREATE INDEX idx_clients_name ON clients(name);
CREATE INDEX idx_clients_active ON clients(is_active);

-- Language pair indexes
CREATE INDEX idx_language_pairs_source ON language_pairs(source_language);
CREATE INDEX idx_language_pairs_target ON language_pairs(target_language);

-- Rate indexes
CREATE INDEX idx_rates_translator ON translator_rates(translator_id);
CREATE INDEX idx_rates_client ON translator_rates(client_id) WHERE client_id IS NOT NULL;
CREATE INDEX idx_rates_language_pair ON translator_rates(language_pair_id);
CREATE INDEX idx_rates_category ON translator_rates(match_category_id);
CREATE INDEX idx_rates_lookup ON translator_rates(translator_id, language_pair_id, match_category_id);

-- Project indexes
CREATE INDEX idx_projects_translator ON projects(translator_id);
CREATE INDEX idx_projects_client ON projects(client_id) WHERE client_id IS NOT NULL;
CREATE INDEX idx_projects_language_pair ON projects(language_pair_id);
CREATE INDEX idx_projects_created ON projects(created_at);

-- Project file indexes
CREATE INDEX idx_project_files_project ON project_files(project_id);
CREATE INDEX idx_project_files_filename ON project_files(filename);
CREATE INDEX idx_project_files_hash ON project_files(file_hash) WHERE file_hash IS NOT NULL;

-- =============================================================================
-- AUTOMATIC UPDATE TRIGGERS
-- =============================================================================

-- Translators update timestamp
CREATE TRIGGER trg_translators_updated_at
    AFTER UPDATE ON translators
    BEGIN
        UPDATE translators SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Clients update timestamp  
CREATE TRIGGER trg_clients_updated_at
    AFTER UPDATE ON clients
    BEGIN
        UPDATE clients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Rates update timestamp
CREATE TRIGGER trg_rates_updated_at
    AFTER UPDATE ON translator_rates
    BEGIN
        UPDATE translator_rates SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Projects update timestamp
CREATE TRIGGER trg_projects_updated_at
    AFTER UPDATE ON projects
    BEGIN
        UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- App settings update timestamp
CREATE TRIGGER trg_settings_updated_at
    AFTER UPDATE ON app_settings
    BEGIN
        UPDATE app_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- =============================================================================
-- INITIAL REFERENCE DATA
-- =============================================================================

-- Default match categories in display order
INSERT INTO match_categories (name, display_order) VALUES
('Context Match', 1),
('Repetitions', 2),
('100%', 3),
('95% - 99%', 4),
('85% - 94%', 5),
('75% - 84%', 6),
('50% - 74%', 7),
('No Match', 8),
('MT Match', 9);

-- Common language pairs
INSERT INTO language_pairs (source_language, target_language) VALUES
('en', 'de'), ('de', 'en'),
('en', 'fr'), ('fr', 'en'),
('en', 'es'), ('es', 'en'),
('en', 'it'), ('it', 'en'),
('en', 'pt'), ('pt', 'en'),
('de', 'fr'), ('fr', 'de'),
('de', 'es'), ('es', 'de'),
('lv', 'et'), ('et', 'lv'),
('en', 'lv'), ('lv', 'en'),
('en', 'et'), ('et', 'en');

-- Default application settings
INSERT INTO app_settings (setting_key, setting_value, setting_type, description) VALUES
('default_mt_percentage', '70', 'integer', 'Default MT percentage for 100% matches'),
('default_currency', 'EUR', 'string', 'Default currency for rates'),
('backup_retention_days', '30', 'integer', 'Number of days to retain database backups'),
('max_file_size_mb', '50', 'integer', 'Maximum file size for uploads in MB'),
('enable_auto_backup', 'true', 'boolean', 'Enable automatic database backups'),
('app_version', '1.0.0', 'string', 'Current application version'),
('last_backup_date', '', 'string', 'Last automatic backup date'),
('ui_theme', 'default', 'string', 'User interface theme'),
('decimal_places_rate', '4', 'integer', 'Decimal places for rate display'),
('decimal_places_cost', '2', 'integer', 'Decimal places for cost display');