# DEV HANDOFF: Story 3.6 Expansion & Inline Flagging

**Date:** 2025-11-06
**From:** John (Product Manager)
**To:** James (Dev Agent)
**Priority:** 🔴 P0 - BLOCKS PRODUCTION DEPLOYMENT
**Estimated Effort:** 3.5-4 days

---

## 📋 EXECUTIVE SUMMARY

**What:** Reopen and expand Story 3.6 (Declaration Review Form) to display all 77 fields from `VietnameseDeclarationData` schema + add inline correction flagging feature.

**Why:** Current form only displays 25/77 fields (33% coverage), blocking users from editing critical customs declaration data. User also needs ability to flag corrections with reasoning for AI improvement.

**Impact:** CRITICAL - Blocks production deployment. Users cannot submit accurate declarations without complete field coverage.

**Good News:** ✅ Backend already extracts and stores all 77 fields correctly. This is primarily frontend work with minor backend additions.

---

## 🎯 OBJECTIVES

1. **Expand form structure:** 4 sections → 12 collapsible sections
2. **Expand field coverage:** 25 fields → 77 fields (complete customs declaration)
3. **Add inline flagging:** Flag button on every field → popover → corrections log
4. **Add validation:** All 77 fields required before approval
5. **Add UX improvements:** Section completion indicators, null field placeholders

**Keep Working:**
- ✅ Confidence color-coding (green/yellow/red)
- ✅ Auto-save every 5 seconds
- ✅ React Hook Form + Zod validation
- ✅ All existing tests

---

## 📊 CURRENT STATE vs TARGET STATE

### Current State (Story 3.6 as "Done")
```
DeclarationForm:
  └── 4 sections (Company Info, Shipment, Products, Tax)
      └── ~25 editable fields
      └── Confidence indicators ✅
      └── Auto-save ✅
      └── Validation warnings panel ✅
```

### Target State (Story 3.6 Reopened)
```
DeclarationForm:
  └── 12 collapsible sections (all match VietnameseDeclarationData schema)
      └── 77 editable fields
      └── Confidence indicators ✅
      └── Auto-save ✅
      └── Validation warnings panel ✅
      └── Section completion indicators (NEW)
      └── Null field placeholders (NEW)
      └── Flag button on every field (NEW)
          └── Flag popover with category + notes
          └── Corrections log panel
          └── CSV export
```

---

## 🗂️ FILES TO MODIFY

### Frontend (Primary Work)

| File | Action | Complexity |
|------|--------|------------|
| `docs/stories/3.6-declaration-review-form.story.md` | Update ACs, add tasks 16-32 | Low |
| `frontend/src/components/declarations/declaration-form.tsx` | Expand from 4 → 12 sections, add 77 fields | **HIGH** |
| `frontend/src/types/declaration.ts` | Add complete DraftData interface (77 fields) | Medium |
| `frontend/src/lib/validators.ts` | Extend Zod schema for all 77 fields | Medium |
| `frontend/src/components/declarations/field-flag-button.tsx` | **NEW** - Flag button + popover | Medium |
| `frontend/src/components/declarations/corrections-log-panel.tsx` | **NEW** - Corrections table panel | Medium |
| `frontend/src/components/declarations/null-field-placeholder.tsx` | **NEW** - Null field indicator | Low |
| `frontend/src/hooks/use-declaration.ts` | Add corrections query + createCorrection mutation | Low |
| `frontend/src/lib/api.ts` | Add createCorrection, getCorrections functions | Low |
| `frontend/src/__tests__/unit/components/declarations/declaration-form.test.tsx` | Update tests for 12 sections + flagging | Medium |

### Backend (Minor Work)

| File | Action | Complexity |
|------|--------|------------|
| `backend/src/models/correction.py` | Add `correction_category`, `notes` columns | Low |
| `backend/alembic/versions/` | **NEW** - Migration for corrections table | Low |
| `backend/src/api/v1/corrections.py` | **NEW** - POST/GET corrections endpoints | Medium |
| `backend/src/schemas/correction.py` | **NEW** - CorrectionCreate, CorrectionResponse schemas | Low |
| `backend/src/api/v1/declarations.py` | Add approval validation (all 77 fields) | Medium |

### Documentation

| File | Action | Complexity |
|------|--------|------------|
| `docs/prd/requirements.md` | Update FR10, FR12, FR15 | Low |
| `docs/stories/3.8-declaration-approval-export.story.md` | Update AC2 (approval validation) | Low |

---

## 📝 DETAILED TASK BREAKDOWN

### Phase 1: Form Expansion (Day 1) - 1 day

**Goal:** Expand form to 12 sections with all 77 fields visible and editable.

#### Task 16: Expand Form to 12 Sections
**File:** `frontend/src/components/declarations/declaration-form.tsx`

**Current Structure:**
```tsx
// Simplified - 4 sections
<form>
  <Collapsible title="Company Information">
    {/* ~10 fields */}
  </Collapsible>
  <Collapsible title="Shipment Details">
    {/* ~8 fields */}
  </Collapsible>
  <Collapsible title="Product Line Items">
    {/* Table with ~5 columns */}
  </Collapsible>
  <Collapsible title="Tax Calculations">
    {/* ~5 fields */}
  </Collapsible>
</form>
```

**Target Structure:**
```tsx
<form>
  <Collapsible title="Declaration Header" defaultOpen={true}>
    {/* 6 fields: declarationTypeCode, customsOfficeCode, processingDivisionCode, registrationDate, representativeHScode */}
    {/* declarationNumber is read-only, show as disabled field */}
  </Collapsible>

  <Collapsible title="Importer Information" defaultOpen={false}>
    {/* 5 fields: taxCode, name, postalCode, address, phone */}
  </Collapsible>

  <Collapsible title="Exporter Information" defaultOpen={false}>
    {/* 5 fields: name, addressLine1, addressLine2, addressLine3, countryCode */}
  </Collapsible>

  <Collapsible title="Shipping & Transport" defaultOpen={false}>
    {/* 10 fields: billOfLadingNumber, warehouseCode, warehouseName,
         portOfDischargeCode, portOfDischargeName, portOfLoadingCode,
         portOfLoadingName, transportModeCode, vesselName, arrivalDate */}
  </Collapsible>

  <Collapsible title="Package & Container" defaultOpen={false}>
    {/* 6 fields: totalPackages, packageUnit, packageMarks,
         grossWeightKg, grossWeightUnit, containerCount */}
  </Collapsible>

  <Collapsible title="Invoice Details" defaultOpen={false}>
    {/* 8 fields: invoiceNumber, invoiceDate, paymentMethodCode,
         invoiceTotal, invoiceCurrency, invoiceIncoterm,
         totalTaxableValueVnd, exchangeRate */}
  </Collapsible>

  <Collapsible title="Certificate of Origin" defaultOpen={false}>
    {/* 3 fields: coFormType, coNumber, coDate */}
  </Collapsible>

  <Collapsible title="Product Line Items" defaultOpen={false}>
    {/* Table with 18 columns per product */}
    {/* Use react-hook-form's useFieldArray for dynamic rows */}
  </Collapsible>

  <Collapsible title="Import Duty" defaultOpen={false}>
    {/* 4 fields: rate, rateType, amount, exemptionAmount */}
  </Collapsible>

  <Collapsible title="VAT & Other Taxes" defaultOpen={false}>
    {/* 6 fields: name, rateCode, rate, taxableValueVnd, amount, exemptionAmount */}
  </Collapsible>

  <Collapsible title="Tax Summary" defaultOpen={false}>
    {/* 4 fields: totalTaxAmountVnd, taxPaymentDeadlineCode,
         taxpayerType, taxClassification */}
  </Collapsible>

  <Collapsible title="Metadata" defaultOpen={false}>
    {/* 2 fields (read-only): totalPages, totalLineItems */}
    {/* Show as disabled fields with info icon */}
  </Collapsible>
</form>
```

**Implementation Steps:**
1. Copy backend field names from `backend/src/schemas/vietnamese_declaration.py`
2. Create 12 Collapsible components matching schema structure
3. Use existing `ConfidenceInput` wrapper for each field (already handles color-coding)
4. Set `defaultOpen={true}` only for Declaration Header
5. Map field paths correctly: `draft_data.declaration_header.customs_office_code`

**Testing:**
- Verify all 12 sections render
- Verify collapse/expand works for each section
- Verify fields pre-populate with data from `draft_data`

---

#### Task 19: Implement Section Completion Tracking
**Files:**
- `frontend/src/components/declarations/declaration-form.tsx`
- `frontend/src/lib/form-utils.ts` (NEW - helper functions)

**Goal:** Show "✓ Complete (5/5)" or "⚠️ Incomplete (3/5)" badge in each section header.

**Implementation:**
```tsx
// Helper function
function calculateSectionCompletion(
  fields: string[],
  formValues: any
): { completed: number; total: number } {
  const completed = fields.filter(fieldPath => {
    const value = getNestedValue(formValues, fieldPath);
    return value !== null && value !== undefined && value !== '';
  }).length;

  return { completed, total: fields.length };
}

// Usage in Collapsible header
<Collapsible>
  <CollapsibleTrigger>
    <div className="flex items-center justify-between w-full">
      <span>Declaration Header</span>
      <CompletionBadge
        completed={completion.completed}
        total={completion.total}
      />
    </div>
  </CollapsibleTrigger>
  {/* ... fields ... */}
</Collapsible>

// CompletionBadge component
function CompletionBadge({ completed, total }: { completed: number; total: number }) {
  const isComplete = completed === total;

  return (
    <Badge variant={isComplete ? "success" : "warning"}>
      {isComplete ? "✓" : "⚠️"} {completed}/{total}
    </Badge>
  );
}
```

**Use React Hook Form's `watch()`** to reactively update completion as user fills fields.

---

#### Task 18: Add Null/Missing Field Indicators
**Files:**
- `frontend/src/components/declarations/null-field-placeholder.tsx` (NEW)
- `frontend/src/components/declarations/confidence-input.tsx` (MODIFY)

**Goal:** Show "⚠️ Not extracted - manual entry required" for null fields.

**Implementation:**
```tsx
// NullFieldPlaceholder.tsx
export function NullFieldPlaceholder({ fieldName }: { fieldName: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-2 rounded">
      <AlertTriangle className="h-4 w-4" />
      <span>Not extracted - manual entry required</span>
    </div>
  );
}

// Update ConfidenceInput to handle null values
export function ConfidenceInput({ value, confidence, ...props }: ConfidenceInputProps) {
  const isNull = value === null || value === undefined || value === '';
  const borderColor = isNull
    ? 'border-red-500'
    : getConfidenceBorderColor(confidence);

  return (
    <div className="space-y-1">
      {isNull && <NullFieldPlaceholder fieldName={props.name} />}
      <Input
        value={value ?? ''}
        className={cn('border-2', borderColor)}
        placeholder={isNull ? "Enter manually..." : ""}
        {...props}
      />
    </div>
  );
}
```

---

### Phase 2: Inline Flagging UI (Day 2) - 1 day

**Goal:** Add flag button to every field with popover for correction notes.

#### Task 22: Create Inline Flag Button Component
**File:** `frontend/src/components/declarations/field-flag-button.tsx` (NEW)

**Implementation:**
```tsx
import { Flag } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useDeclaration } from '@/hooks/use-declaration';

interface FieldFlagButtonProps {
  declarationId: string;
  fieldName: string;
  originalValue: string | null;
  correctedValue: string;
}

const CORRECTION_CATEGORIES = [
  'AI Extraction Error',
  'Wrong HS Code',
  'Calculation Error',
  'Missing Data',
  'Format Issue',
  'Other'
] as const;

export function FieldFlagButton({
  declarationId,
  fieldName,
  originalValue,
  correctedValue
}: FieldFlagButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [category, setCategory] = useState<string>('');
  const [notes, setNotes] = useState('');
  const { createCorrection } = useDeclaration(declarationId);

  const handleSave = async () => {
    if (!category) return;

    await createCorrection.mutateAsync({
      field_name: fieldName,
      original_value: originalValue,
      corrected_value: correctedValue,
      correction_category: category,
      notes: notes || null
    });

    setIsOpen(false);
    setCategory('');
    setNotes('');
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 ml-2"
          type="button"
        >
          <Flag className="h-3.5 w-3.5 text-orange-600" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        <div className="space-y-4">
          <div>
            <h4 className="font-medium mb-2">Flag Correction</h4>
            <p className="text-sm text-muted-foreground mb-4">
              Help us improve by explaining why you corrected this field.
            </p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Correction Category</label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger>
                <SelectValue placeholder="Select category..." />
              </SelectTrigger>
              <SelectContent>
                {CORRECTION_CATEGORIES.map(cat => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Notes (optional)</label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value.slice(0, 500))}
              placeholder="Additional details..."
              className="h-20"
            />
            <p className="text-xs text-muted-foreground text-right">
              {notes.length}/500
            </p>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleSave}
              disabled={!category || createCorrection.isPending}
              className="flex-1"
            >
              {createCorrection.isPending ? 'Saving...' : 'Save Flag'}
            </Button>
            <Button
              variant="outline"
              onClick={() => setIsOpen(false)}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
```

---

#### Task 29: Integrate Flag Button Into All Form Fields
**File:** `frontend/src/components/declarations/declaration-form.tsx`

**Update ConfidenceInput wrapper to include flag button:**
```tsx
<div className="flex items-center">
  <ConfidenceInput
    name="declaration_header.customs_office_code"
    label="Customs Office Code"
    value={formValues.declaration_header?.customs_office_code}
    confidence={confidenceScores?.['declaration_header.customs_office_code'] ?? 0}
    {...register('declaration_header.customs_office_code')}
  />
  <FieldFlagButton
    declarationId={declarationId}
    fieldName="declaration_header.customs_office_code"
    originalValue={extractedData?.declaration_header?.customs_office_code}
    correctedValue={formValues.declaration_header?.customs_office_code}
  />
</div>
```

**For product array fields:**
```tsx
{fields.map((field, index) => (
  <div key={field.id} className="flex items-center">
    <ConfidenceInput
      name={`products.${index}.hs_code`}
      label="HS Code"
      {...register(`products.${index}.hs_code`)}
    />
    <FieldFlagButton
      fieldName={`products.${index}.hs_code`}
      originalValue={extractedData?.products?.[index]?.hs_code}
      correctedValue={formValues.products?.[index]?.hs_code}
    />
  </div>
))}
```

---

### Phase 3: Backend + Corrections Log (Day 3) - 1 day

**Goal:** Create corrections API, extend database, build corrections log panel.

#### Task 25: Extend Backend Corrections Table
**File:** `backend/src/models/correction.py`

**Add two columns:**
```python
correction_category: Mapped[str] = mapped_column(
    String(50),
    nullable=False,
    index=True,
    comment="Category: AI Extraction Error, Wrong HS Code, etc."
)
notes: Mapped[Optional[str]] = mapped_column(
    Text,
    nullable=True,
    comment="Optional user notes (max 500 chars)"
)
```

**Create migration:**
```bash
cd backend
alembic revision --autogenerate -m "Add correction_category and notes to corrections table"
alembic upgrade head
```

---

#### Task 26: Create Corrections API Endpoints
**File:** `backend/src/api/v1/corrections.py` (NEW)

See complete code in Sprint Change Proposal Section 3, Artifact 8.

**Key endpoints:**
- `POST /api/declarations/{id}/corrections` - Create correction flag
- `GET /api/declarations/{id}/corrections` - Get all corrections (JSON or CSV)

**Don't forget to register router in `backend/src/main.py`:**
```python
from src.api.v1 import corrections

app.include_router(corrections.router)
```

---

#### Task 24: Create Corrections Log Panel
**File:** `frontend/src/components/declarations/corrections-log-panel.tsx` (NEW)

**Implementation:**
```tsx
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import { useDeclaration } from '@/hooks/use-declaration';
import { formatDistanceToNow } from 'date-fns';

export function CorrectionsLogPanel({ declarationId }: { declarationId: string }) {
  const { corrections } = useDeclaration(declarationId);

  const handleExportCSV = async () => {
    const response = await fetch(
      `/api/declarations/${declarationId}/corrections?format=csv`,
      { credentials: 'include' }
    );
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `corrections_${declarationId}.csv`;
    a.click();
  };

  if (!corrections || corrections.length === 0) {
    return null; // Don't show panel if no corrections
  }

  return (
    <Collapsible defaultOpen={false} className="border rounded-lg p-4 mb-6">
      <CollapsibleTrigger className="flex items-center justify-between w-full">
        <h3 className="text-lg font-semibold">
          Corrections Log ({corrections.length} flagged fields)
        </h3>
        <Button variant="ghost" size="sm">
          Toggle
        </Button>
      </CollapsibleTrigger>

      <CollapsibleContent className="mt-4">
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button variant="outline" size="sm" onClick={handleExportCSV}>
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Field Name</TableHead>
                <TableHead>Original → Corrected</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Notes</TableHead>
                <TableHead>Flagged By</TableHead>
                <TableHead>Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {corrections.map((correction) => (
                <TableRow key={correction.id}>
                  <TableCell className="font-mono text-sm">
                    {formatFieldName(correction.field_name)}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground line-through">
                        {correction.original_value || 'null'}
                      </span>
                      <span>→</span>
                      <span className="font-medium">
                        {correction.corrected_value}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm bg-orange-100 text-orange-800 px-2 py-1 rounded">
                      {correction.correction_category}
                    </span>
                  </TableCell>
                  <TableCell className="max-w-xs truncate">
                    {correction.notes || '-'}
                  </TableCell>
                  <TableCell>{correction.user_name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDistanceToNow(new Date(correction.timestamp), { addSuffix: true })}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

function formatFieldName(fieldPath: string): string {
  // Convert "declaration_header.customs_office_code" to "Declaration Header › Customs Office Code"
  const parts = fieldPath.split('.');
  return parts.map(p =>
    p.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  ).join(' › ');
}
```

**Add to review page:**
```tsx
// In frontend/src/app/declarations/[id]/review/page.tsx

<ValidationWarningsPanel warnings={declaration.validation_warnings} />
<CorrectionsLogPanel declarationId={declaration.id} />  {/* NEW */}
<DeclarationForm {...props} />
```

---

### Phase 4: Testing & QA (Day 4 - Half) - 0.75 day

#### Task 30-31: Update Tests

**Update `declaration-form.test.tsx`:**
```tsx
describe('DeclarationForm - Expanded', () => {
  it('renders all 12 sections', () => {
    render(<DeclarationForm {...mockProps} />);

    expect(screen.getByText('Declaration Header')).toBeInTheDocument();
    expect(screen.getByText('Importer Information')).toBeInTheDocument();
    expect(screen.getByText('Exporter Information')).toBeInTheDocument();
    // ... test all 12 sections
  });

  it('shows completion indicator for incomplete sections', () => {
    const mockData = {
      declaration_header: {
        customs_office_code: 'TEST',
        // Other 5 fields null
      }
    };

    render(<DeclarationForm data={mockData} />);
    expect(screen.getByText('⚠️ 1/6')).toBeInTheDocument();
  });

  it('disables approve button when fields incomplete', () => {
    const mockData = { /* some fields null */ };
    render(<DeclarationForm data={mockData} />);

    const approveButton = screen.getByText('Approve');
    expect(approveButton).toBeDisabled();
  });
});
```

**Create `field-flag-button.test.tsx`:**
```tsx
describe('FieldFlagButton', () => {
  it('opens popover on click', async () => {
    render(<FieldFlagButton {...mockProps} />);

    const flagButton = screen.getByRole('button');
    await userEvent.click(flagButton);

    expect(screen.getByText('Flag Correction')).toBeInTheDocument();
  });

  it('saves correction with category and notes', async () => {
    const mockCreateCorrection = vi.fn();
    render(<FieldFlagButton {...mockProps} />);

    await userEvent.click(screen.getByRole('button'));
    await userEvent.selectOptions(screen.getByLabelText('Correction Category'), 'Wrong HS Code');
    await userEvent.type(screen.getByPlaceholderText('Additional details...'), 'Should be 96190014');
    await userEvent.click(screen.getByText('Save Flag'));

    expect(mockCreateCorrection).toHaveBeenCalledWith({
      field_name: 'products.0.hs_code',
      correction_category: 'Wrong HS Code',
      notes: 'Should be 96190014'
    });
  });
});
```

---

## 🔧 TECHNICAL NOTES

### 1. Field Mapping Reference

**Backend Schema Location:** `backend/src/schemas/vietnamese_declaration.py`

**Frontend Type Location:** `frontend/src/types/declaration.ts`

**Ensure 1:1 mapping:**
- Backend: `declaration_header.customs_office_code`
- Frontend: `draft_data.declaration_header.customs_office_code`
- Form field name: `declaration_header.customs_office_code`

### 2. React Hook Form Tips

**For nested objects:**
```tsx
register('declaration_header.customs_office_code')
```

**For arrays:**
```tsx
const { fields, append, remove } = useFieldArray({
  control,
  name: 'products'
});

fields.map((field, index) => (
  <input {...register(`products.${index}.hs_code`)} />
))
```

**Watch for completion tracking:**
```tsx
const formValues = watch(); // Get all form values
// Recalculates whenever any field changes
```

### 3. TanStack Query Pattern

**Add to `useDeclaration` hook:**
```tsx
// Query for corrections
const correctionsQuery = useQuery({
  queryKey: ['declarations', id, 'corrections'],
  queryFn: () => apiClient.getCorrections(id),
  enabled: !!id
});

// Mutation for creating correction
const createCorrection = useMutation({
  mutationFn: (data: CorrectionCreate) =>
    apiClient.createCorrection(id, data),
  onSuccess: () => {
    // Invalidate corrections query to refetch
    queryClient.invalidateQueries(['declarations', id, 'corrections']);
  }
});

return {
  ...declarationQuery,
  corrections: correctionsQuery.data?.corrections,
  createCorrection
};
```

### 4. API Client Functions

**Add to `frontend/src/lib/api.ts`:**
```typescript
export async function createCorrection(
  declarationId: string,
  data: CorrectionCreate
): Promise<CorrectionResponse> {
  const response = await apiClient.post(
    `/api/declarations/${declarationId}/corrections`,
    data
  );
  return response.data;
}

export async function getCorrections(
  declarationId: string
): Promise<CorrectionListResponse> {
  const response = await apiClient.get(
    `/api/declarations/${declarationId}/corrections`
  );
  return response.data;
}
```

---

## ✅ DEFINITION OF DONE CHECKLIST

### Functionality
- [ ] All 12 sections visible in form
- [ ] All 77 fields editable (except metadata read-only)
- [ ] Sections collapsible (only Declaration Header open by default)
- [ ] Section completion indicators working ("✓ 5/5" or "⚠️ 3/5")
- [ ] Null fields show "⚠️ Not extracted" placeholder
- [ ] Null fields have red border
- [ ] Approve button disabled if any field null/empty
- [ ] Approve button shows tooltip with missing field count
- [ ] Flag button appears on all 77 fields
- [ ] Flag popover opens with category dropdown + notes textarea
- [ ] Flag saves successfully (POST /api/corrections)
- [ ] Flagged fields show 🚩 badge in label
- [ ] Corrections Log panel displays all corrections
- [ ] CSV export downloads corrections data
- [ ] Auto-save still works (every 5 seconds)
- [ ] Confidence colors still work (green/yellow/red)
- [ ] Validation warnings panel still works

### Backend
- [ ] Corrections table migration applied successfully
- [ ] POST /api/declarations/{id}/corrections endpoint working
- [ ] GET /api/declarations/{id}/corrections endpoint working
- [ ] CSV export format correct (all columns present)
- [ ] Approval validation blocks if fields incomplete
- [ ] Approval error message lists missing fields

### Testing
- [ ] All existing tests passing (no regressions)
- [ ] New tests for 12 sections
- [ ] New tests for completion indicators
- [ ] New tests for null field placeholders
- [ ] New tests for approval validation
- [ ] New tests for flag button + popover
- [ ] New tests for corrections log panel
- [ ] Integration test: flag field → save → see in log → export CSV

### Documentation
- [ ] Story 3.6 updated with new ACs and tasks
- [ ] PRD updated (FR10, FR12, FR15)
- [ ] Story 3.8 updated (AC2 approval validation)
- [ ] Story 4.1 updated (integration note about corrections table)

### Code Quality
- [ ] No console.errors or warnings
- [ ] No TypeScript errors
- [ ] No ESLint errors
- [ ] All imports resolved
- [ ] No unused variables
- [ ] Proper error handling for API calls
- [ ] Loading states for all async operations

---

## 🚨 COMMON PITFALLS & HOW TO AVOID

### 1. Field Path Mapping Errors
**Problem:** Form field doesn't save because path doesn't match backend structure.

**Solution:**
- Always use exact field paths from `VietnameseDeclarationData` schema
- Test field path: `console.log(formValues.declaration_header?.customs_office_code)`
- Verify backend receives correct structure in PATCH request

### 2. React Hook Form Array Fields
**Problem:** Product table rows don't update correctly.

**Solution:**
- Use `useFieldArray` for products array
- Always use `field.id` as React key (not index)
- Register fields as `products.${index}.field_name`

### 3. TanStack Query Cache Invalidation
**Problem:** Corrections don't show in log after saving.

**Solution:**
- Call `queryClient.invalidateQueries()` in mutation's `onSuccess`
- Use correct query key: `['declarations', id, 'corrections']`

### 4. Null vs Empty String
**Problem:** Field shows as complete but value is empty string `""`.

**Solution:**
- Check for both: `value === null || value === undefined || value === ''`
- Backend validation should reject empty strings too

### 5. Performance with 77 Fields
**Problem:** Form feels slow when typing.

**Solution:**
- React Hook Form already uses uncontrolled inputs (good!)
- Don't call `watch()` unnecessarily (only for completion indicators)
- Consider React.memo() for Collapsible sections if needed

---

## 📞 SUPPORT & QUESTIONS

If you encounter blockers or have questions:

1. **Check Sprint Change Proposal** - Full detailed specs in `.ai/handoff-story-3.6-expansion.md`
2. **Backend Schema Reference** - `backend/src/schemas/vietnamese_declaration.py` is source of truth
3. **Existing Code** - `frontend/src/components/declarations/declaration-form.tsx` (current implementation)
4. **PM Assistance** - Tag John if requirements unclear

---

## 🎯 SUCCESS CRITERIA

**This handoff is successful when:**
1. ✅ User can see and edit all 77 fields in declaration review form
2. ✅ User can flag any field with correction reasoning
3. ✅ Corrections are logged and exportable as CSV
4. ✅ Approval is blocked until all 77 fields are complete
5. ✅ All existing functionality still works (no regressions)
6. ✅ QA review passes

**Good luck, James! You've got this! 🚀**

---

**End of Handoff Document**
