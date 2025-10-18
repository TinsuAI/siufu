# Database Schema

The database uses PostgreSQL 18.0 with JSONB for flexible data, audit columns on all tables, and strategic indexing for performance.

## Complete SQL Schema (DDL)

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_crypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Custom Types
CREATE TYPE user_role AS ENUM ('processor', 'admin');
CREATE TYPE declaration_status AS ENUM (
    'UPLOADED', 'PROCESSING', 'VALIDATING',
    'READY_FOR_REVIEW', 'APPROVED', 'REJECTED', 'FAILED'
);
CREATE TYPE correction_type AS ENUM (
    'TYPO', 'WRONG_EXTRACTION', 'WRONG_HS_CODE',
    'VALIDATION_FIX', 'OTHER'
);
CREATE TYPE knowledge_base_type AS ENUM ('GOOD_LIST', 'TARIFF');
CREATE TYPE knowledge_base_status AS ENUM ('ACTIVE', 'ARCHIVED');

-- Organizations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'processor',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization ON users(organization_id);

-- Declarations
CREATE TABLE declarations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status declaration_status NOT NULL DEFAULT 'UPLOADED',
    uploaded_files JSONB NOT NULL DEFAULT '[]'::jsonb,
    extracted_data JSONB,
    draft_data JSONB,
    validation_warnings JSONB DEFAULT '[]'::jsonb,
    confidence_scores JSONB DEFAULT '{}'::jsonb,
    processing_progress FLOAT DEFAULT 0.0,
    processing_error TEXT,
    approved_by_user_id UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_declarations_status ON declarations(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_declarations_created_at ON declarations(created_at DESC);
CREATE INDEX idx_declarations_draft_data ON declarations USING GIN (draft_data);

-- Knowledge Base Versions
CREATE TABLE knowledge_base_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type knowledge_base_type NOT NULL,
    version_number INTEGER NOT NULL,
    record_count INTEGER NOT NULL DEFAULT 0,
    file_path VARCHAR(500) NOT NULL,
    status knowledge_base_status NOT NULL DEFAULT 'ACTIVE',
    rollback_reason TEXT,
    uploaded_by_user_id UUID NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    UNIQUE(organization_id, type, version_number)
);

-- Good List Entries
CREATE TABLE good_list_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_description TEXT NOT NULL,
    hs_code VARCHAR(8) NOT NULL,
    price_usd DECIMAL(12, 2),
    weight_kg DECIMAL(10, 3),
    supplier VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    version_id UUID NOT NULL REFERENCES knowledge_base_versions(id) ON DELETE CASCADE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trigram index for fuzzy matching
CREATE INDEX idx_goodlist_description_trgm ON good_list_entries
    USING GIN (product_description gin_trgm_ops);

-- Tariff Rates
CREATE TABLE tariff_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hs_code VARCHAR(8) NOT NULL,
    vat_rate DECIMAL(5, 4) NOT NULL,
    import_duty_rate DECIMAL(5, 4) NOT NULL,
    trade_agreement VARCHAR(50),
    description_vi TEXT,
    description_en TEXT,
    effective_date DATE NOT NULL,
    version_id UUID NOT NULL REFERENCES knowledge_base_versions(id) ON DELETE CASCADE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tariff_hs_code ON tariff_rates(hs_code) WHERE is_active = TRUE;

-- Corrections
CREATE TABLE corrections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    declaration_id UUID NOT NULL REFERENCES declarations(id) ON DELETE CASCADE,
    field_name VARCHAR(255) NOT NULL,
    original_value TEXT NOT NULL,
    corrected_value TEXT NOT NULL,
    original_confidence DECIMAL(3, 2),
    correction_type correction_type NOT NULL DEFAULT 'OTHER',
    source_document VARCHAR(50),
    metadata JSONB DEFAULT '{}'::jsonb,
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_corrections_field_name ON corrections(field_name);
CREATE INDEX idx_corrections_created_at ON corrections(created_at DESC);

-- Triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_declarations_updated_at BEFORE UPDATE ON declarations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Key Design Decisions:**
- **JSONB for flexible data**: `draft_data`, `extracted_data`, `uploaded_files` use JSONB for schema flexibility
- **Soft deletes**: `deleted_at` timestamp instead of hard deletes
- **Trigram indexes**: Enable fast fuzzy matching on product descriptions
- **Audit columns**: `created_at`, `updated_at`, `created_by_user_id` on all tables

---
