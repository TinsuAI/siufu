# DEV HANDOFF: Master Data Management for Importers & Exporters

**Date:** 2025-11-07
**From:** John (Product Manager)
**To:** James (Dev Agent)
**Priority:** 🟡 P1 - High Priority (Performance & UX Improvement)
**Estimated Effort:** 4-5 days

---

## 📋 EXECUTIVE SUMMARY

**What:** Create master data tables for Importers and Exporters to eliminate redundant AI extraction and ensure consistent company data across declarations.

**Why:**
- **Cost reduction:** Stop re-extracting the same importer/exporter data on every declaration
- **Data consistency:** Prevent "ABC Corp" being extracted differently in different declarations
- **Learning from corrections:** When user fixes importer address in Declaration #1, auto-populate corrected data in Declaration #2
- **Better UX:** Show "✅ Verified Company" badge for known importers/exporters

**Impact:** HIGH - Reduces GPT-4 Vision costs by ~15-20% (importer/exporter fields = ~10 of 77 fields), improves data quality, and significantly improves user experience for repeat customers.

---

## 🎯 OBJECTIVES

1. **Create master data tables:** `importers` and `exporters` tables with all relevant fields
2. **Auto-matching on extraction:** When AI extracts tax code, check if importer exists → use master data
3. **Learning system:** On declaration approval, save/update importer/exporter to master table
4. **Fuzzy matching:** Use tax code (primary) + name fuzzy match (fallback) for matching
5. **Master data UI:** Add pages to view, search, manually add/edit, and merge duplicate companies
6. **Badge indicators:** Show "✅ Verified" or "⚠️ New - Review Required" badges in form

---

## 📊 CURRENT STATE vs TARGET STATE

### Current State
```
User uploads Declaration #1:
  ├── AI extracts: "ABC Corp" (tax: 0123456789)
  ├── User reviews & corrects address
  └── Approved ✅

User uploads Declaration #2 (same importer):
  ├── AI extracts: "ABC Corp" AGAIN ❌ (wasting API cost)
  ├── User reviews & corrects SAME address AGAIN ❌
  └── Approved ✅
```

### Target State
```
User uploads Declaration #1:
  ├── AI extracts: "ABC Corp" (tax: 0123456789)
  ├── Backend checks: Importer tax_code=0123456789 exists? NO
  ├── User reviews & corrects address
  └── Approved ✅ → Save to master table "importers"

User uploads Declaration #2 (same importer):
  ├── AI extracts tax_code: "0123456789"
  ├── Backend checks: Importer exists? YES ✅
  ├── Skip AI extraction, use master data
  ├── Show "✅ Verified Company" badge
  ├── Pre-fill all fields from master
  └── User can still override if needed
```

---

## 🗂️ DATABASE SCHEMA

### New Tables

#### 1. `importers` Table

```sql
CREATE TABLE importers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core identification
    tax_code VARCHAR(20) UNIQUE NOT NULL,  -- Vietnamese MST (10 digits)
    name VARCHAR(500) NOT NULL,
    name_normalized VARCHAR(500) NOT NULL,  -- Lowercase, no accents for fuzzy matching

    -- Contact info
    postal_code VARCHAR(20),
    address TEXT,
    phone VARCHAR(50),

    -- Metadata
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    first_seen_declaration_id UUID REFERENCES declarations(id) ON DELETE SET NULL,
    last_seen_declaration_id UUID REFERENCES declarations(id) ON DELETE SET NULL,
    declaration_count INT DEFAULT 1,  -- How many declarations use this importer

    -- Quality tracking
    is_verified BOOLEAN DEFAULT false,  -- Manual verification by user
    confidence_score FLOAT DEFAULT 0.0,  -- Average confidence from all declarations
    last_reviewed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    last_reviewed_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,  -- Soft delete

    -- Indexes
    INDEX idx_importers_tax_code (tax_code),
    INDEX idx_importers_name_normalized (name_normalized),
    INDEX idx_importers_org_id (organization_id),
    INDEX idx_importers_deleted_at (deleted_at)
);
```

#### 2. `exporters` Table

```sql
CREATE TABLE exporters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core identification
    name VARCHAR(500) NOT NULL,
    name_normalized VARCHAR(500) NOT NULL,  -- For fuzzy matching
    country_code CHAR(2) NOT NULL,  -- ISO 3166-1 alpha-2

    -- Address
    address_line1 TEXT,
    address_line2 TEXT,
    address_line3 TEXT,

    -- Metadata
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    first_seen_declaration_id UUID REFERENCES declarations(id) ON DELETE SET NULL,
    last_seen_declaration_id UUID REFERENCES declarations(id) ON DELETE SET NULL,
    declaration_count INT DEFAULT 1,

    -- Quality tracking
    is_verified BOOLEAN DEFAULT false,
    confidence_score FLOAT DEFAULT 0.0,
    last_reviewed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    last_reviewed_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Indexes
    INDEX idx_exporters_name_normalized (name_normalized),
    INDEX idx_exporters_country_code (country_code),
    INDEX idx_exporters_org_id (organization_id),
    INDEX idx_exporters_deleted_at (deleted_at),

    -- Unique constraint on normalized name + country (within org)
    UNIQUE (organization_id, name_normalized, country_code)
);
```

#### 3. Add Foreign Keys to `declarations` Table

```sql
ALTER TABLE declarations
ADD COLUMN importer_id UUID REFERENCES importers(id) ON DELETE SET NULL,
ADD COLUMN exporter_id UUID REFERENCES exporters(id) ON DELETE SET NULL;

CREATE INDEX idx_declarations_importer_id ON declarations(importer_id);
CREATE INDEX idx_declarations_exporter_id ON declarations(exporter_id);
```

---

## 🔍 MATCHING ALGORITHM

### Importer Matching Logic

```python
def match_importer(
    extracted_tax_code: str | None,
    extracted_name: str | None,
    organization_id: UUID
) -> Importer | None:
    """
    Match extracted importer data to existing master record.

    Priority:
    1. Exact tax_code match (most reliable)
    2. Fuzzy name match (fallback for data entry errors)
    """

    # Strategy 1: Tax Code Match (Primary)
    if extracted_tax_code:
        # Normalize tax code (remove spaces, dashes)
        normalized_tax = normalize_tax_code(extracted_tax_code)

        importer = db.query(Importer).filter(
            Importer.tax_code == normalized_tax,
            Importer.organization_id == organization_id,
            Importer.deleted_at.is_(None)
        ).first()

        if importer:
            return importer

    # Strategy 2: Fuzzy Name Match (Fallback)
    if extracted_name:
        normalized_name = normalize_company_name(extracted_name)

        # Use Levenshtein distance or trigram similarity
        candidates = db.query(Importer).filter(
            Importer.organization_id == organization_id,
            Importer.deleted_at.is_(None)
        ).all()

        for candidate in candidates:
            similarity = calculate_similarity(
                normalized_name,
                candidate.name_normalized
            )

            # If 85%+ similar, likely a match
            if similarity >= 0.85:
                return candidate

    return None  # No match found


def normalize_tax_code(tax_code: str) -> str:
    """Remove spaces, dashes, convert to uppercase"""
    return re.sub(r'[^A-Z0-9]', '', tax_code.upper())


def normalize_company_name(name: str) -> str:
    """
    Lowercase, remove accents, remove special chars, trim spaces

    Examples:
    - "Công ty TNHH ABC" → "cong ty tnhh abc"
    - "ABC Corp.,  Ltd." → "abc corp ltd"
    """
    import unicodedata

    # Remove accents
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('utf-8')

    # Lowercase
    name = name.lower()

    # Remove special characters
    name = re.sub(r'[^a-z0-9\s]', '', name)

    # Collapse multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()

    return name


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity between two strings using Levenshtein distance.
    Returns float 0.0-1.0 (1.0 = identical)
    """
    from difflib import SequenceMatcher
    return SequenceMatcher(None, str1, str2).ratio()
```

### Exporter Matching Logic

```python
def match_exporter(
    extracted_name: str | None,
    extracted_country_code: str | None,
    organization_id: UUID
) -> Exporter | None:
    """
    Match exported exporter data to existing master record.

    Uses name + country_code composite matching since exporters
    typically don't have Vietnamese tax codes.
    """

    if not extracted_name or not extracted_country_code:
        return None

    normalized_name = normalize_company_name(extracted_name)

    # Strategy 1: Exact match (name + country)
    exporter = db.query(Exporter).filter(
        Exporter.name_normalized == normalized_name,
        Exporter.country_code == extracted_country_code.upper(),
        Exporter.organization_id == organization_id,
        Exporter.deleted_at.is_(None)
    ).first()

    if exporter:
        return exporter

    # Strategy 2: Fuzzy name match within same country
    candidates = db.query(Exporter).filter(
        Exporter.country_code == extracted_country_code.upper(),
        Exporter.organization_id == organization_id,
        Exporter.deleted_at.is_(None)
    ).all()

    for candidate in candidates:
        similarity = calculate_similarity(
            normalized_name,
            candidate.name_normalized
        )

        if similarity >= 0.85:
            return candidate

    return None
```

---

## 🔄 DECLARATION PROCESSING FLOW (UPDATED)

### Phase 1: Extraction (Modified)

```python
# In backend/src/services/extraction_service.py

async def process_declaration(declaration_id: UUID):
    """Updated extraction flow with master data lookup"""

    # Step 1: AI extraction (as before)
    extracted_data = await extract_with_gpt4_vision(declaration.uploaded_files)

    # Step 2: Match importer (NEW)
    importer = match_importer(
        extracted_tax_code=extracted_data['importer']['tax_code'],
        extracted_name=extracted_data['importer']['name'],
        organization_id=declaration.organization_id
    )

    if importer:
        # ✅ Use master data instead of AI-extracted data
        extracted_data['importer'] = {
            'tax_code': importer.tax_code,
            'name': importer.name,
            'postal_code': importer.postal_code,
            'address': importer.address,
            'phone': importer.phone
        }

        # Boost confidence scores (master data is more reliable)
        extracted_data['confidence_scores']['importer.tax_code'] = 1.0
        extracted_data['confidence_scores']['importer.name'] = 1.0
        extracted_data['confidence_scores']['importer.address'] = 1.0
        extracted_data['confidence_scores']['importer.postal_code'] = 1.0
        extracted_data['confidence_scores']['importer.phone'] = 1.0

        # Link declaration to importer
        declaration.importer_id = importer.id

        # Update importer stats
        importer.declaration_count += 1
        importer.last_seen_declaration_id = declaration.id
        importer.updated_at = datetime.now()

    # Step 3: Match exporter (NEW)
    exporter = match_exporter(
        extracted_name=extracted_data['exporter']['name'],
        extracted_country_code=extracted_data['exporter']['country_code'],
        organization_id=declaration.organization_id
    )

    if exporter:
        # ✅ Use master data
        extracted_data['exporter'] = {
            'name': exporter.name,
            'address_line1': exporter.address_line1,
            'address_line2': exporter.address_line2,
            'address_line3': exporter.address_line3,
            'country_code': exporter.country_code
        }

        # Boost confidence
        extracted_data['confidence_scores']['exporter.name'] = 1.0
        extracted_data['confidence_scores']['exporter.country_code'] = 1.0
        # ... other exporter fields

        # Link declaration
        declaration.exporter_id = exporter.id

        # Update stats
        exporter.declaration_count += 1
        exporter.last_seen_declaration_id = declaration.id
        exporter.updated_at = datetime.now()

    # Step 4: Save extracted data
    declaration.extracted_data = extracted_data
    declaration.draft_data = extracted_data.copy()  # Initialize draft

    db.commit()
```

### Phase 2: Approval (Modified)

```python
# In backend/src/api/v1/declarations.py

@router.post("/declarations/{id}/approve")
async def approve_declaration(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve declaration and save/update master data"""

    declaration = get_declaration_or_404(db, id)

    # Step 1: Validate all fields complete (existing logic)
    validate_complete_declaration(declaration.draft_data)

    # Step 2: Update/create importer master record (NEW)
    importer_data = declaration.draft_data['importer']

    if declaration.importer_id:
        # Update existing importer with corrected data
        importer = db.query(Importer).get(declaration.importer_id)
        importer.name = importer_data['name']
        importer.name_normalized = normalize_company_name(importer_data['name'])
        importer.address = importer_data['address']
        importer.postal_code = importer_data['postal_code']
        importer.phone = importer_data['phone']
        importer.last_reviewed_by_user_id = current_user.id
        importer.last_reviewed_at = datetime.now()
        importer.updated_at = datetime.now()
    else:
        # Create new importer
        importer = Importer(
            tax_code=normalize_tax_code(importer_data['tax_code']),
            name=importer_data['name'],
            name_normalized=normalize_company_name(importer_data['name']),
            postal_code=importer_data['postal_code'],
            address=importer_data['address'],
            phone=importer_data['phone'],
            organization_id=declaration.organization_id,
            first_seen_declaration_id=declaration.id,
            last_seen_declaration_id=declaration.id,
            declaration_count=1,
            confidence_score=declaration.confidence_scores.get('importer.name', 0.0),
            is_verified=True,  # User approved it
            last_reviewed_by_user_id=current_user.id,
            last_reviewed_at=datetime.now()
        )
        db.add(importer)
        db.flush()
        declaration.importer_id = importer.id

    # Step 3: Update/create exporter master record (NEW)
    exporter_data = declaration.draft_data['exporter']

    if declaration.exporter_id:
        # Update existing
        exporter = db.query(Exporter).get(declaration.exporter_id)
        exporter.name = exporter_data['name']
        exporter.name_normalized = normalize_company_name(exporter_data['name'])
        exporter.address_line1 = exporter_data['address_line1']
        exporter.address_line2 = exporter_data['address_line2']
        exporter.address_line3 = exporter_data['address_line3']
        exporter.country_code = exporter_data['country_code']
        exporter.last_reviewed_by_user_id = current_user.id
        exporter.last_reviewed_at = datetime.now()
        exporter.updated_at = datetime.now()
    else:
        # Create new exporter
        exporter = Exporter(
            name=exporter_data['name'],
            name_normalized=normalize_company_name(exporter_data['name']),
            address_line1=exporter_data['address_line1'],
            address_line2=exporter_data['address_line2'],
            address_line3=exporter_data['address_line3'],
            country_code=exporter_data['country_code'],
            organization_id=declaration.organization_id,
            first_seen_declaration_id=declaration.id,
            last_seen_declaration_id=declaration.id,
            declaration_count=1,
            confidence_score=declaration.confidence_scores.get('exporter.name', 0.0),
            is_verified=True,
            last_reviewed_by_user_id=current_user.id,
            last_reviewed_at=datetime.now()
        )
        db.add(exporter)
        db.flush()
        declaration.exporter_id = exporter.id

    # Step 4: Mark declaration approved (existing logic)
    declaration.status = DeclarationStatus.APPROVED
    declaration.approved_by_user_id = current_user.id
    declaration.approved_at = datetime.now()

    db.commit()

    return {"message": "Declaration approved successfully"}
```

---

## 🎨 FRONTEND CHANGES

### 1. Badge Indicators in Declaration Form

**File:** `frontend/src/components/declarations/declaration-form.tsx`

```tsx
// Add company badge component
function CompanyBadge({ isVerified, declarationCount }: {
  isVerified: boolean;
  declarationCount?: number;
}) {
  if (isVerified) {
    return (
      <Badge variant="success" className="ml-2">
        <CheckCircle className="h-3 w-3 mr-1" />
        Verified Company
        {declarationCount && ` (${declarationCount} declarations)`}
      </Badge>
    );
  }

  return (
    <Badge variant="warning" className="ml-2">
      <AlertTriangle className="h-3 w-3 mr-1" />
      New Company - Review Required
    </Badge>
  );
}

// Update Importer section header
<Collapsible title="Importer Information">
  <CollapsibleTrigger>
    <div className="flex items-center justify-between w-full">
      <span>Importer Information</span>
      <div className="flex items-center gap-2">
        <CompletionBadge completed={5} total={5} />
        {declaration.importer_id && (
          <CompanyBadge
            isVerified={true}
            declarationCount={importerData?.declaration_count}
          />
        )}
      </div>
    </div>
  </CollapsibleTrigger>
  {/* ... fields ... */}
</Collapsible>
```

### 2. Show Master Data Source in Tooltips

```tsx
<ConfidenceInput
  name="importer.tax_code"
  label="Tax Code"
  value={formValues.importer?.tax_code}
  confidence={confidenceScores?.['importer.tax_code'] ?? 0}
  tooltip={
    declaration.importer_id
      ? "Data from verified company record"
      : "AI-extracted data - please review"
  }
  {...register('importer.tax_code')}
/>
```

---

## 📄 MASTER DATA MANAGEMENT UI

### Page 1: Companies Directory

**Route:** `/companies`

**Features:**
- Tabs: "Importers" | "Exporters"
- Search by name, tax code
- Filters: Verified/Unverified, Country (exporters)
- Sort by: Name, Declaration count, Last seen
- Actions: View details, Edit, Merge, Delete

**Wireframe:**
```
┌────────────────────────────────────────────────────────────┐
│  Companies                                          [+ Add] │
├────────────────────────────────────────────────────────────┤
│  [Importers] [Exporters]                                   │
│                                                             │
│  🔍 Search by name or tax code...    [Filter ▾] [Sort ▾]  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ ✅ ABC Corp (0123456789)               [Edit] [Merge]│ │
│  │    15 declarations • Last seen: 2 days ago            │ │
│  │    📍 Hanoi, Vietnam                                  │ │
│  ├───────────────────────────────────────────────────────┤ │
│  │ ⚠️  XYZ Trading (0987654321)           [Edit] [Merge]│ │
│  │    3 declarations • Last seen: 1 week ago             │ │
│  │    📍 Ho Chi Minh City, Vietnam                       │ │
│  └───────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Implementation:**

```tsx
// frontend/src/app/companies/page.tsx

export default function CompaniesPage() {
  const [tab, setTab] = useState<'importers' | 'exporters'>('importers');
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'verified' | 'unverified'>('all');

  const { data: companies, isLoading } = useQuery({
    queryKey: ['companies', tab, search, filter],
    queryFn: () => apiClient.getCompanies({ type: tab, search, filter })
  });

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Companies</h1>
        <Button onClick={() => router.push('/companies/new')}>
          <Plus className="h-4 w-4 mr-2" />
          Add Company
        </Button>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="importers">Importers</TabsTrigger>
          <TabsTrigger value="exporters">Exporters</TabsTrigger>
        </TabsList>

        <TabsContent value={tab}>
          <div className="flex gap-4 mb-6">
            <Input
              placeholder={`Search ${tab}...`}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1"
            />
            <Select value={filter} onValueChange={setFilter}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Companies</SelectItem>
                <SelectItem value="verified">Verified Only</SelectItem>
                <SelectItem value="unverified">Unverified Only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {isLoading ? (
            <LoadingSpinner />
          ) : (
            <div className="space-y-4">
              {companies?.map((company) => (
                <CompanyCard
                  key={company.id}
                  company={company}
                  type={tab}
                />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### Page 2: Company Details/Edit

**Route:** `/companies/[id]`

**Features:**
- View all company details
- Edit all fields
- See linked declarations (table with links)
- Mark as verified/unverified
- Delete company (with warning)

### Page 3: Merge Duplicates Tool

**Route:** `/companies/merge`

**Features:**
- Auto-detect potential duplicates using fuzzy matching
- Show side-by-side comparison
- Select which record to keep
- Preview merge result
- Confirm merge

**Algorithm for finding duplicates:**

```python
# backend/src/api/v1/companies.py

@router.get("/companies/duplicates")
async def find_duplicate_companies(
    type: Literal['importers', 'exporters'],
    organization_id: UUID,
    db: Session = Depends(get_db)
):
    """Find potential duplicate company records"""

    if type == 'importers':
        companies = db.query(Importer).filter(
            Importer.organization_id == organization_id,
            Importer.deleted_at.is_(None)
        ).all()
    else:
        companies = db.query(Exporter).filter(
            Exporter.organization_id == organization_id,
            Exporter.deleted_at.is_(None)
        ).all()

    duplicates = []

    for i, company1 in enumerate(companies):
        for company2 in companies[i+1:]:
            similarity = calculate_similarity(
                company1.name_normalized,
                company2.name_normalized
            )

            # If 80%+ similar, likely duplicate
            if similarity >= 0.80:
                duplicates.append({
                    'company1': company1,
                    'company2': company2,
                    'similarity': similarity,
                    'reason': 'Similar name'
                })

    # Sort by similarity (highest first)
    duplicates.sort(key=lambda x: x['similarity'], reverse=True)

    return duplicates
```

---

## 📋 DETAILED TASK BREAKDOWN

### Phase 1: Database & Backend Core (Days 1-2)

#### Task 1: Create Database Models
**Files:**
- `backend/src/models/importer.py` (NEW)
- `backend/src/models/exporter.py` (NEW)

**Implementation:**
```python
# backend/src/models/importer.py

from datetime import datetime
import uuid
from typing import Optional

from sqlalchemy import String, Float, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import Base


class Importer(Base):
    """Master data table for importers"""

    __tablename__ = "importers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Core identification
    tax_code: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    name_normalized: Mapped[str] = mapped_column(
        String(500), nullable=False, index=True
    )

    # Contact info
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadata
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    first_seen_declaration_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("declarations.id", ondelete="SET NULL"),
        nullable=True
    )
    last_seen_declaration_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("declarations.id", ondelete="SET NULL"),
        nullable=True
    )
    declaration_count: Mapped[int] = mapped_column(Integer, default=1)

    # Quality tracking
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    last_reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    declarations: Mapped[list["Declaration"]] = relationship(
        "Declaration",
        foreign_keys="[Declaration.importer_id]",
        back_populates="importer"
    )

    def __repr__(self) -> str:
        return f"<Importer(id={self.id}, name={self.name}, tax_code={self.tax_code})>"
```

Similar implementation for `backend/src/models/exporter.py`.

#### Task 2: Create Database Migration
```bash
cd backend
alembic revision --autogenerate -m "Add importers and exporters master data tables"
alembic upgrade head
```

#### Task 3: Create Matching Service
**File:** `backend/src/services/master_data_service.py` (NEW)

Implement the matching algorithms described in "MATCHING ALGORITHM" section above.

#### Task 4: Update Extraction Service
**File:** `backend/src/services/extraction_service.py`

Add master data lookup logic after AI extraction (see "DECLARATION PROCESSING FLOW" section).

#### Task 5: Update Approval Endpoint
**File:** `backend/src/api/v1/declarations.py`

Add save/update master data logic on approval (see "DECLARATION PROCESSING FLOW" section).

---

### Phase 2: Companies API Endpoints (Day 3)

#### Task 6: Create Companies CRUD Endpoints
**File:** `backend/src/api/v1/companies.py` (NEW)

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Literal

from src.api.deps import get_db, get_current_user
from src.models.importer import Importer
from src.models.exporter import Exporter
from src.schemas.company import CompanyListResponse, CompanyDetail, CompanyCreate, CompanyUpdate

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("/")
async def list_companies(
    type: Literal['importers', 'exporters'],
    search: str | None = None,
    filter: Literal['all', 'verified', 'unverified'] = 'all',
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CompanyListResponse:
    """List all companies (importers or exporters)"""

    if type == 'importers':
        query = db.query(Importer).filter(
            Importer.organization_id == current_user.organization_id,
            Importer.deleted_at.is_(None)
        )

        if search:
            query = query.filter(
                (Importer.name.ilike(f'%{search}%')) |
                (Importer.tax_code.ilike(f'%{search}%'))
            )

        if filter == 'verified':
            query = query.filter(Importer.is_verified == True)
        elif filter == 'unverified':
            query = query.filter(Importer.is_verified == False)

        total = query.count()
        companies = query.offset(skip).limit(limit).all()

    else:  # exporters
        query = db.query(Exporter).filter(
            Exporter.organization_id == current_user.organization_id,
            Exporter.deleted_at.is_(None)
        )

        if search:
            query = query.filter(Exporter.name.ilike(f'%{search}%'))

        if filter == 'verified':
            query = query.filter(Exporter.is_verified == True)
        elif filter == 'unverified':
            query = query.filter(Exporter.is_verified == False)

        total = query.count()
        companies = query.offset(skip).limit(limit).all()

    return CompanyListResponse(
        total=total,
        companies=[CompanyDetail.from_orm(c) for c in companies]
    )


@router.get("/{id}")
async def get_company(
    id: UUID,
    type: Literal['importers', 'exporters'],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CompanyDetail:
    """Get company details"""

    if type == 'importers':
        company = db.query(Importer).filter(
            Importer.id == id,
            Importer.organization_id == current_user.organization_id,
            Importer.deleted_at.is_(None)
        ).first()
    else:
        company = db.query(Exporter).filter(
            Exporter.id == id,
            Exporter.organization_id == current_user.organization_id,
            Exporter.deleted_at.is_(None)
        ).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return CompanyDetail.from_orm(company)


@router.post("/")
async def create_company(
    type: Literal['importers', 'exporters'],
    data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CompanyDetail:
    """Manually create a new company"""

    if type == 'importers':
        company = Importer(
            tax_code=normalize_tax_code(data.tax_code),
            name=data.name,
            name_normalized=normalize_company_name(data.name),
            postal_code=data.postal_code,
            address=data.address,
            phone=data.phone,
            organization_id=current_user.organization_id,
            is_verified=True,
            last_reviewed_by_user_id=current_user.id,
            last_reviewed_at=datetime.now()
        )
    else:
        company = Exporter(
            name=data.name,
            name_normalized=normalize_company_name(data.name),
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            address_line3=data.address_line3,
            country_code=data.country_code,
            organization_id=current_user.organization_id,
            is_verified=True,
            last_reviewed_by_user_id=current_user.id,
            last_reviewed_at=datetime.now()
        )

    db.add(company)
    db.commit()
    db.refresh(company)

    return CompanyDetail.from_orm(company)


@router.patch("/{id}")
async def update_company(
    id: UUID,
    type: Literal['importers', 'exporters'],
    data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CompanyDetail:
    """Update company details"""

    # Get company
    if type == 'importers':
        company = db.query(Importer).filter(
            Importer.id == id,
            Importer.organization_id == current_user.organization_id,
            Importer.deleted_at.is_(None)
        ).first()
    else:
        company = db.query(Exporter).filter(
            Exporter.id == id,
            Exporter.organization_id == current_user.organization_id,
            Exporter.deleted_at.is_(None)
        ).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Update fields
    for field, value in data.dict(exclude_unset=True).items():
        setattr(company, field, value)

    # Update normalized name if name changed
    if 'name' in data.dict(exclude_unset=True):
        company.name_normalized = normalize_company_name(company.name)

    company.last_reviewed_by_user_id = current_user.id
    company.last_reviewed_at = datetime.now()
    company.updated_at = datetime.now()

    db.commit()
    db.refresh(company)

    return CompanyDetail.from_orm(company)


@router.delete("/{id}")
async def delete_company(
    id: UUID,
    type: Literal['importers', 'exporters'],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete company"""

    if type == 'importers':
        company = db.query(Importer).filter(
            Importer.id == id,
            Importer.organization_id == current_user.organization_id,
            Importer.deleted_at.is_(None)
        ).first()
    else:
        company = db.query(Exporter).filter(
            Exporter.id == id,
            Exporter.organization_id == current_user.organization_id,
            Exporter.deleted_at.is_(None)
        ).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Soft delete
    company.deleted_at = datetime.now()
    db.commit()

    return {"message": "Company deleted successfully"}


@router.get("/duplicates")
async def find_duplicates(
    type: Literal['importers', 'exporters'],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Find potential duplicate companies"""

    # See "MATCHING ALGORITHM" section for implementation
    pass


@router.post("/merge")
async def merge_companies(
    type: Literal['importers', 'exporters'],
    keep_id: UUID,
    merge_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Merge two companies (keep one, delete other, update declarations)"""

    # 1. Get both companies
    # 2. Update all declarations from merge_id to point to keep_id
    # 3. Update keep_id.declaration_count
    # 4. Soft delete merge_id
    pass
```

Register router in `backend/src/main.py`.

---

### Phase 3: Frontend UI (Days 4-5)

#### Task 7: Add Badge Indicators to Declaration Form
**File:** `frontend/src/components/declarations/declaration-form.tsx`

See "FRONTEND CHANGES" section above for implementation.

#### Task 8: Create Companies List Page
**File:** `frontend/src/app/companies/page.tsx` (NEW)

See "MASTER DATA MANAGEMENT UI" section above.

#### Task 9: Create Company Details/Edit Page
**File:** `frontend/src/app/companies/[id]/page.tsx` (NEW)

#### Task 10: Create Merge Duplicates Tool
**File:** `frontend/src/app/companies/merge/page.tsx` (NEW)

---

## ✅ DEFINITION OF DONE CHECKLIST

### Backend
- [ ] `importers` table created with all fields
- [ ] `exporters` table created with all fields
- [ ] Migration applied successfully
- [ ] `declarations.importer_id` and `declarations.exporter_id` columns added
- [ ] Matching service implemented (tax code + fuzzy name)
- [ ] Extraction service updated to check master data
- [ ] Approval endpoint updated to save/update master data
- [ ] Companies CRUD API endpoints working
- [ ] Duplicate detection endpoint working
- [ ] Merge companies endpoint working

### Frontend
- [ ] Badge indicators showing in declaration form ("✅ Verified" or "⚠️ New")
- [ ] Companies list page showing importers/exporters
- [ ] Search and filters working
- [ ] Company details/edit page working
- [ ] Manual add company working
- [ ] Merge duplicates tool working
- [ ] Navigation menu updated with "Companies" link

### Testing
- [ ] Unit tests for matching algorithms
- [ ] Unit tests for normalization functions
- [ ] Integration test: Extract → Match existing importer → Use master data
- [ ] Integration test: Approve declaration → Create new importer
- [ ] Integration test: Approve declaration → Update existing importer
- [ ] Integration test: Merge two companies → Declarations updated

### Documentation
- [ ] PRD updated with master data management feature
- [ ] API documentation updated
- [ ] User guide for managing companies

---

## 🚨 COMMON PITFALLS & HOW TO AVOID

### 1. Fuzzy Matching Too Aggressive
**Problem:** System merges "ABC Corp" with "ABC Corporation" but they're actually different companies.

**Solution:**
- Use 85% threshold (not lower)
- Always show user confirmation before auto-matching
- Allow user to unlink declaration from importer

### 2. Race Condition on Approval
**Problem:** Two users approve declarations with same new importer simultaneously → duplicate importers created.

**Solution:**
- Use database unique constraint on `tax_code`
- Handle `IntegrityError` and retry with existing record

### 3. Performance with Large Company Lists
**Problem:** Fuzzy matching all companies for every declaration is slow.

**Solution:**
- Use database indexes on `name_normalized`
- Limit fuzzy search to top 100 candidates sorted by name similarity
- Consider full-text search (PostgreSQL `tsvector`)

---

## 📞 SUPPORT & QUESTIONS

If you encounter blockers:
1. Check this handoff document for detailed specs
2. Review matching algorithm implementations carefully
3. Test with real Vietnamese company names (accents matter!)
4. PM assistance available - tag John if requirements unclear

---

## 🎯 SUCCESS CRITERIA

**This feature is successful when:**
1. ✅ System recognizes repeat importers/exporters and uses master data
2. ✅ AI extraction costs reduced by ~15-20%
3. ✅ Users see "✅ Verified Company" badge for known companies
4. ✅ User corrections to company data persist across declarations
5. ✅ Users can manage companies via dedicated UI
6. ✅ Duplicate detection helps maintain clean master data
7. ✅ All existing functionality still works (no regressions)

**Good luck! This is a high-impact feature that will significantly improve the system! 🚀**

---

**End of Handoff Document**
