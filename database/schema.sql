-- Translation Cost Calculator - Database Schema
-- Complete SQLite schema with proper relationships and constraints
-- Version: 1.0
-- Created: 2025-01-04

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- =============================================================================
-- CORE ENTITY TABLES
-- =============================================================================

-- Translators table
CREATE TABLE IF NOT EXISTS translators (
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
    
    -- Constraints
    CONSTRAINT ck_translator_name_length CHECK (LENGTH(TRIM(name)) >= 2),
    CONSTRAINT ck_translator_email_format CHECK (
        email IS NULL OR 
        (email LIKE '%@%.%' AND LENGTH(email) >= 5)
    ),
    
    -- Indexes
    UNIQUE(name)
);

-- Clients table
CREATE TABLE IF NOT EXISTS clients (
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
    
    -- Constraints
    CONSTRAINT ck_client_name_length CHECK (LENGTH(TRIM(name)) >= 2),
    CONSTRAINT ck_client_email_format CHECK (
        email IS NULL OR 
        (email LIKE '%@%.%' AND LENGTH(email) >= 5)
    ),
    
    -- Indexes
    UNIQUE(name)
);

-- Language pairs table
CREATE TABLE IF NOT EXISTS language_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_language TEXT NOT NULL,
    target_language TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT ck_language_codes_valid CHECK (
        LENGTH(TRIM(source_language)) >= 2 AND
        LENGTH(TRIM(target_language)) >= 2 AND
        TRIM(source_language) != TRIM(target_language)
    ),
    
    -- Indexes
    UNIQUE(source_language, target_language)
);

-- Match categories table
CREATE TABLE IF NOT EXISTS match_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT ck_category_name_length CHECK (LENGTH(TRIM(name)) >= 1),
    CONSTRAINT ck_display_order_positive CHECK (display_order > 0)
);

-- =============================================================================
-- RATE SYSTEM TABLES
-- =============================================================================

-- Translator rates table with hierarchical support
CREATE TABLE IF NOT EXISTS translator_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    translator_id INTEGER NOT NULL,
    client_id INTEGER NULL, -- NULL for general rates
    language_pair_id INTEGER NOT NULL,
    match_category_id INTEGER NOT NULL,
    rate_per_word DECIMAL(10,4) NOT NULL DEFAULT 0.0000,
    minimum_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    is_minimum_fee_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    currency TEXT NOT NULL DEFAULT 'EUR',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (translator_id) REFERENCES translators(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (language_pair_id) REFERENCES language_pairs(id) ON DELETE RESTRICT,
    FOREIGN KEY (match_category_id) REFERENCES match_categories(id) ON DELETE RESTRICT,
    
    -- Business constraints
    CONSTRAINT ck_rate_positive CHECK (rate_per_word >= 0.0000),
    CONSTRAINT ck_minimum_fee_positive CHECK (minimum_fee >= 0.00),
    CONSTRAINT ck_currency_code CHECK (LENGTH(TRIM(currency)) = 3),
    
    -- Unique constraint for rate hierarchy
    UNIQUE(translator_id, client_id, language_pair_id, match_category_id)
);

-- =============================================================================
-- PROJECT SYSTEM TABLES
-- =============================================================================

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    translator_id INTEGER NOT NULL,
    client_id INTEGER NULL,
    language_pair_id INTEGER NOT NULL,
    mt_percentage INTEGER NOT NULL DEFAULT 70,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (translator_id) REFERENCES translators(id) ON DELETE RESTRICT,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL,
    FOREIGN KEY (language_pair_id) REFERENCES language_pairs(id) ON DELETE RESTRICT,
    
    -- Business constraints
    CONSTRAINT ck_project_name_length CHECK (LENGTH(TRIM(name)) >= 1),
    CONSTRAINT ck_mt_percentage_range CHECK (mt_percentage >= 0 AND mt_percentage <= 100)
);

-- Project files table
CREATE TABLE IF NOT EXISTS project_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    parsed_data TEXT NOT NULL, -- JSON serialized FileAnalysisData
    file_size INTEGER DEFAULT 0,
    file_hash TEXT, -- For duplicate detection
    cat_tool TEXT, -- Source CAT tool (Trados, Phrase, etc.)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Business constraints
    CONSTRAINT ck_filename_length CHECK (LENGTH(TRIM(filename)) >= 1),
    CONSTRAINT ck_file_path_length CHECK (LENGTH(TRIM(file_path)) >= 1),
    CONSTRAINT ck_parsed_data_not_empty CHECK (LENGTH(TRIM(parsed_data)) >= 1),
    CONSTRAINT ck_file_size_positive CHECK (file_size >= 0)
);

-- =============================================================================
-- SYSTEM TABLES
-- =============================================================================

-- Migration tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    description TEXT,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT ck_version_format CHECK (LENGTH(TRIM(version)) >= 1)
);

-- Application settings table
CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    setting_type TEXT NOT NULL DEFAULT 'string', -- string, integer, boolean, decimal
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    
    -- Constraints
    CONSTRAINT ck_setting_key_length CHECK (LENGTH(TRIM(setting_key)) >= 1),
    CONSTRAINT ck_setting_type_valid CHECK (
        setting_type IN ('string', 'integer', 'boolean', 'decimal', 'json')
    )
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Translator indexes
CREATE INDEX IF NOT EXISTS idx_translators_name ON translators(name);
CREATE INDEX IF NOT EXISTS idx_translators_active ON translators(is_active);
CREATE INDEX IF NOT EXISTS idx_translators_email ON translators(email) WHERE email IS NOT NULL;

-- Client indexes
CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name);
CREATE INDEX IF NOT EXISTS idx_clients_active ON clients(is_active);

-- Language pair indexes
CREATE INDEX IF NOT EXISTS idx_language_pairs_source ON language_pairs(source_language);
CREATE INDEX IF NOT EXISTS idx_language_pairs_target ON language_pairs(target_language);

-- Rate indexes
CREATE INDEX IF NOT EXISTS idx_rates_translator ON translator_rates(translator_id);
CREATE INDEX IF NOT EXISTS idx_rates_client ON translator_rates(client_id) WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_rates_language_pair ON translator_rates(language_pair_id);
CREATE INDEX IF NOT EXISTS idx_rates_category ON translator_rates(match_category_id);
CREATE INDEX IF NOT EXISTS idx_rates_lookup ON translator_rates(translator_id, language_pair_id, match_category_id);

-- Project indexes
CREATE INDEX IF NOT EXISTS idx_projects_translator ON projects(translator_id);
CREATE INDEX IF NOT EXISTS idx_projects_client ON projects(client_id) WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_projects_language_pair ON projects(language_pair_id);
CREATE INDEX IF NOT EXISTS idx_projects_created ON projects(created_at);

-- Project file indexes
CREATE INDEX IF NOT EXISTS idx_project_files_project ON project_files(project_id);
CREATE INDEX IF NOT EXISTS idx_project_files_filename ON project_files(filename);
CREATE INDEX IF NOT EXISTS idx_project_files_hash ON project_files(file_hash) WHERE file_hash IS NOT NULL;

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Complete translator information with rate counts
CREATE VIEW IF NOT EXISTS v_translators_summary AS
SELECT 
    t.id,
    t.name,
    t.email,
    t.company,
    t.is_active,
    t.created_at,
    COUNT(DISTINCT r.id) as rate_count,
    COUNT(DISTINCT p.id) as project_count
FROM translators t
LEFT JOIN translator_rates r ON t.id = r.translator_id
LEFT JOIN projects p ON t.id = p.translator_id
GROUP BY t.id, t.name, t.email, t.company, t.is_active, t.created_at;

-- Project summary with file and word counts
CREATE VIEW IF NOT EXISTS v_projects_summary AS
SELECT 
    p.id,
    p.name,
    p.created_at,
    t.name as translator_name,
    c.name as client_name,
    lp.source_language,
    lp.target_language,
    p.mt_percentage,
    COUNT(pf.id) as file_count,
    -- Note: word_count calculation would require parsing JSON, 
    -- will be calculated in application layer
    0 as total_words
FROM projects p
JOIN translators t ON p.translator_id = t.id
LEFT JOIN clients c ON p.client_id = c.id
JOIN language_pairs lp ON p.language_pair_id = lp.id
LEFT JOIN project_files pf ON p.id = pf.project_id
GROUP BY p.id, p.name, p.created_at, t.name, c.name, 
         lp.source_language, lp.target_language, p.mt_percentage;

-- Rate hierarchy view for easy lookups
CREATE VIEW IF NOT EXISTS v_rates_hierarchy AS
SELECT 
    r.id,
    r.translator_id,
    t.name as translator_name,
    r.client_id,
    c.name as client_name,
    r.language_pair_id,
    lp.source_language,
    lp.target_language,
    r.match_category_id,
    mc.name as category_name,
    mc.display_order,
    r.rate_per_word,
    r.minimum_fee,
    r.is_minimum_fee_enabled,
    r.currency,
    CASE 
        WHEN r.client_id IS NOT NULL THEN 1 
        ELSE 2 
    END as priority_level
FROM translator_rates r
JOIN translators t ON r.translator_id = t.id
LEFT JOIN clients c ON r.client_id = c.id
JOIN language_pairs lp ON r.language_pair_id = lp.id
JOIN match_categories mc ON r.match_category_id = mc.id
ORDER BY t.name, lp.source_language, lp.target_language, priority_level, mc.display_order;

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =============================================================================

-- Update timestamp triggers for translators
CREATE TRIGGER IF NOT EXISTS trg_translators_updated_at
    AFTER UPDATE ON translators
    BEGIN
        UPDATE translators SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Update timestamp triggers for clients
CREATE TRIGGER IF NOT EXISTS trg_clients_updated_at
    AFTER UPDATE ON clients
    BEGIN
        UPDATE clients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Update timestamp triggers for rates
CREATE TRIGGER IF NOT EXISTS trg_rates_updated_at
    AFTER UPDATE ON translator_rates
    BEGIN
        UPDATE translator_rates SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Update timestamp triggers for projects
CREATE TRIGGER IF NOT EXISTS trg_projects_updated_at
    AFTER UPDATE ON projects
    BEGIN
        UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Update timestamp triggers for app settings
CREATE TRIGGER IF NOT EXISTS trg_settings_updated_at
    AFTER UPDATE ON app_settings
    BEGIN
        UPDATE app_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- =============================================================================
-- INITIAL DATA SETUP
-- =============================================================================

-- Insert default match categories
INSERT OR IGNORE INTO match_categories (name, display_order) VALUES
('Context Match', 1),
('Repetitions', 2),
('100%', 3),
('95% - 99%', 4),
('85% - 94%', 5),
('75% - 84%', 6),
('50% - 74%', 7),
('No Match', 8),
('MT Match', 9);

-- Insert common language pairs
INSERT OR IGNORE INTO language_pairs (source_language, target_language) VALUES
('en', 'de'), ('de', 'en'),
('en', 'fr'), ('fr', 'en'),
('en', 'es'), ('es', 'en'),
('en', 'it'), ('it', 'en'),
('de', 'fr'), ('fr', 'de');

-- Insert initial application settings
INSERT OR IGNORE INTO app_settings (setting_key, setting_value, setting_type, description) VALUES
('default_mt_percentage', '70', 'integer', 'Default MT percentage for 100% matches'),
('default_currency', 'EUR', 'string', 'Default currency for rates'),
('backup_retention_days', '30', 'integer', 'Number of days to retain database backups'),
('max_file_size_mb', '50', 'integer', 'Maximum file size for uploads in MB'),
('enable_auto_backup', 'true', 'boolean', 'Enable automatic database backups');

-- Record initial schema version
INSERT OR IGNORE INTO schema_migrations (version, description) VALUES
('001', 'Initial database schema with core tables, indexes, views, and triggers');