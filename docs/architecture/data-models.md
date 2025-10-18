# Data Models

This section defines the core business entities and their TypeScript interfaces shared between frontend and backend.

## Model: User

**Purpose:** Represents a customs processing specialist or operations manager who uses the platform. Tracks authentication credentials and audit information for declaration approvals.

**Key Attributes:**
- `id`: UUID - Primary identifier
- `email`: string - Login credential (unique)
- `hashed_password`: string - bcrypt hash (never exposed to frontend)
- `full_name`: string - Display name
- `role`: enum - 'processor' | 'admin' (admin can access analytics)
- `is_active`: boolean - Account status
- `organization_id`: UUID - Foreign key (single org for MVP, prepares for multi-tenant)
- `created_at`: datetime - Account creation timestamp
- `updated_at`: datetime - Last profile update

### TypeScript Interface

```typescript
// Shared type definition (backend generates, frontend imports)
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'processor' | 'admin';
  is_active: boolean;
  organization_id: string;
  created_at: string; // ISO 8601 datetime
  updated_at: string;
}

// Auth response (includes token)
export interface AuthResponse {
  user: User;
  access_token: string;
  token_type: 'bearer';
}
```

### Relationships

- **1:N with Declaration** - One user can process many declarations
- **1:N with Correction** - One user can make many corrections
- **N:1 with Organization** - Many users belong to one organization (future multi-tenant)

---

## Model: Declaration

**Purpose:** Central entity representing a single customs declaration workflow from upload through approval. Stores processing status, extracted data, and audit trail.

**Key Attributes:**
- `id`: UUID - Primary identifier (displayed to user as "Declaration #12345")
- `status`: enum - 'UPLOADED' | 'PROCESSING' | 'VALIDATING' | 'READY_FOR_REVIEW' | 'APPROVED' | 'REJECTED' | 'FAILED'
- `uploaded_files`: JSONB - Metadata for 6 files (filename, size, path, file_type)
- `extracted_data`: JSONB - Raw AI extraction results (flexible schema)
- `draft_data`: JSONB - User-editable declaration data (sync'd with frontend form)
- `validation_warnings`: JSONB[] - Cross-document validation issues with severity
- `confidence_scores`: JSONB - Per-field confidence levels (used for color-coding)
- `processing_progress`: float - 0.0 to 1.0 (for progress bar)
- `processing_error`: string | null - Error message if status = FAILED
- `approved_by_user_id`: UUID | null - FK to User (who clicked "Approve")
- `approved_at`: datetime | null - Timestamp of approval
- `organization_id`: UUID - FK to Organization
- `created_by_user_id`: UUID - FK to User (who uploaded)
- `created_at`: datetime
- `updated_at`: datetime
- `deleted_at`: datetime | null - Soft delete timestamp

### TypeScript Interface

```typescript
export type DeclarationStatus =
  | 'UPLOADED'
  | 'PROCESSING'
  | 'VALIDATING'
  | 'READY_FOR_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'FAILED';

export interface Declaration {
  id: string;
  status: DeclarationStatus;
  uploaded_files: UploadedFile[];
  extracted_data: Record<string, any> | null;
  draft_data: DraftData | null;
  validation_warnings: ValidationWarning[];
  confidence_scores: Record<string, number>;
  processing_progress: number;
  processing_error: string | null;
  approved_by_user_id: string | null;
  approved_at: string | null;
  organization_id: string;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}
```

---

## Model: GoodListEntry

**Purpose:** Historical product data for fuzzy matching. Contains previously processed products with their HS codes, enabling AI to suggest classifications for new products.

**Key Attributes:**
- `id`: UUID - Primary identifier
- `product_description`: string - Product name/description (searchable)
- `hs_code`: string - 8-digit harmonized system code
- `price_usd`: float | null - Historical unit price
- `weight_kg`: float | null - Historical weight
- `supplier`: string | null - Supplier name
- `metadata`: JSONB - Additional flexible data from Excel import
- `version_id`: UUID - FK to KnowledgeBaseVersion (for rollback)
- `organization_id`: UUID - FK to Organization
- `created_at`: datetime
- `is_active`: boolean - False if superseded by new version

---

## Model: TariffRate

**Purpose:** EXIM tariff database containing VAT and import duty rates for each HS code. Used for automatic tax calculation in declarations.

**Key Attributes:**
- `id`: UUID - Primary identifier
- `hs_code`: string - 8-digit (or 2/4/6 for broader categories)
- `vat_rate`: float - Percentage (e.g., 0.08 for 8%)
- `import_duty_rate`: float - Percentage
- `trade_agreement`: string | null - 'ACFTA' | 'ATIGA' | 'STANDARD' (affects rate)
- `description_vi`: string - Vietnamese description
- `description_en`: string - English description
- `version_id`: UUID - FK to KnowledgeBaseVersion
- `organization_id`: UUID - FK to Organization
- `effective_date`: date - When rate became active
- `is_active`: boolean - False if superseded

---

## Model: Correction

**Purpose:** Tracks user edits to AI-generated declarations for continuous learning. Each correction represents a field-level change made during review, capturing original vs corrected values for future model improvement.

**Key Attributes:**
- `id`: UUID - Primary identifier
- `declaration_id`: UUID - FK to Declaration
- `field_name`: string - Dot-notation path (e.g., "products.0.hs_code")
- `original_value`: string - AI-extracted value
- `corrected_value`: string - User-provided value
- `original_confidence`: float - AI confidence (0.0-1.0)
- `correction_type`: enum - 'TYPO' | 'WRONG_EXTRACTION' | 'WRONG_HS_CODE' | 'VALIDATION_FIX' | 'OTHER'
- `source_document`: string | null - Which PDF field came from ('AN' | 'BOL' | 'CO' | 'INVOICE')
- `metadata`: JSONB - Additional context
- `user_id`: UUID - FK to User (who made correction)
- `created_at`: datetime

---

## Model: KnowledgeBaseVersion

**Purpose:** Version control for Good List and Tariff uploads. Enables rollback to previous versions if incorrect data is uploaded.

**Key Attributes:**
- `id`: UUID - Primary identifier
- `type`: enum - 'GOOD_LIST' | 'TARIFF'
- `version_number`: integer - Auto-incrementing version (1, 2, 3...)
- `record_count`: integer - Number of entries in this version
- `file_path`: string - Docker volume path to original Excel file
- `status`: enum - 'ACTIVE' | 'ARCHIVED'
- `uploaded_by_user_id`: UUID - FK to User
- `uploaded_at`: datetime
- `rollback_reason`: string | null - If rolled back, reason provided
- `organization_id`: UUID - FK to Organization

---
