# User Flows

## Flow 1: Process New Declaration (Happy Path)

**User Goal:** Upload 6 files, review AI-generated declaration, and download approved Excel file

**Entry Points:**
- "Upload New" button in primary navigation
- "/upload" direct URL

**Success Criteria:**
- Excel file downloaded with <3 corrections per declaration
- Total time from upload to download under 5 minutes

### Flow Diagram

```mermaid
graph TD
    Start([User clicks Upload New]) --> Login{Authenticated?}
    Login -->|No| LoginScreen[Redirect to Login]
    LoginScreen --> Login
    Login -->|Yes| UploadScreen[Upload Screen]

    UploadScreen --> DragDrop[Drag-drop 6 files]
    DragDrop --> Validate{All 6 files valid?}
    Validate -->|No| Error[Show validation errors]
    Error --> DragDrop
    Validate -->|Yes| Process[Click Process Declaration]

    Process --> Status[Processing Status Screen]
    Status --> Poll{Check status every 2s}
    Poll --> Processing{Status?}
    Processing -->|PROCESSING| Status
    Processing -->|FAILED| ErrorScreen[Show error, allow re-upload]
    Processing -->|READY_FOR_REVIEW| Review[Review & Edit Screen]

    Review --> Inspect[Inspect color-coded fields]
    Inspect --> LowConf{Low confidence fields?}
    LowConf -->|Yes| Edit[Click field, verify in PDF]
    Edit --> Correct[Make inline corrections]
    Correct --> AutoSave[Auto-save every 5s]
    AutoSave --> Inspect
    LowConf -->|No| CheckWarnings{Validation warnings?}

    CheckWarnings -->|Yes| ReviewWarnings[Review warnings panel]
    ReviewWarnings --> Dismiss[Dismiss or correct warnings]
    Dismiss --> CheckWarnings
    CheckWarnings -->|No| Approve[Click Approve button]

    Approve --> Final{Auto-save complete?}
    Final -->|No| Wait[Show tooltip: Wait for save]
    Wait --> Final
    Final -->|Yes| Approved[Declaration approved]

    Approved --> Download[Download Excel button appears]
    Download --> Export[Click Download Excel]
    Export --> Success([Excel file downloaded])
```

### Edge Cases & Error Handling

- **File upload fails (network error):** Show toast notification "Upload failed. Please check your connection and try again." Retry button available.
- **Processing fails (API error):** Status screen shows error message with specific failure reason (e.g., "OCR service unavailable"). Button to retry processing or return to upload.
- **PDF viewer fails to render:** Show placeholder "PDF preview unavailable" with link to download source file directly.
- **Auto-save fails:** Show persistent warning banner "Changes not saved. Please check connection." Retry auto-save every 10s.
- **User navigates away during processing:** Processing continues in background. Return to Declarations list shows "Processing" status. Can click to return to status screen.

**Notes:**
- 90% of declarations follow this happy path
- Average user makes 2-3 corrections per declaration
- Power users complete flow in 2-3 minutes

---

## Flow 2: Handle Low-Confidence Field

**User Goal:** Verify and correct a yellow/red field flagged by AI

**Entry Points:** Review & Edit screen with low-confidence fields present

**Success Criteria:** Field corrected and confidence understood

### Flow Diagram

```mermaid
graph TD
    Start([User on Review screen]) --> Scan[Scan for yellow/red fields]
    Scan --> Focus[Click low-confidence field]

    Focus --> ViewSource[PDF jumps to source location]
    ViewSource --> Compare[Compare PDF vs extracted value]

    Compare --> Match{Values match?}
    Match -->|Yes| Question{Understand why low confidence?}
    Question -->|No| HoverInfo[Hover info icon]
    HoverInfo --> ShowReason[Tooltip: Validation failed or conflicting docs]
    ShowReason --> Accept[Keep value, proceed]
    Question -->|Yes| Accept

    Match -->|No| Edit[Click to edit inline]
    Edit --> TypeCorrect[Type correct value]
    TypeCorrect --> Validate{Valid format?}
    Validate -->|No| ValidationError[Show inline error: HS Code must be 8 digits]
    ValidationError --> TypeCorrect
    Validate -->|Yes| AutoSave[Auto-save triggers]
    AutoSave --> Updated[Field turns green if valid]
    Updated --> Next([Continue to next field])

    Accept --> Next
```

### Edge Cases & Error Handling

- **Source location unavailable (calculated field):** Show tooltip "Calculated field - no source document" instead of jumping to PDF
- **PDF page fails to load:** Show error "Page X unavailable" with option to download full PDF
- **Correction doesn't auto-save:** Show warning icon next to field. User can manually click save button.
- **User enters invalid format:** Inline validation shows specific error (e.g., "Price must be a number")

**Notes:**
- Jump-to-source feature is critical for trust
- Most corrections are typos or OCR errors, not logic errors
- Users appreciate seeing *why* confidence is low

---

## Flow 3: Upload Updated Knowledge Base

**User Goal:** Upload new version of Good List or EXIM Tariff file

**Entry Points:**
- Knowledge Base Management screen
- Navigation: Declarations > Knowledge Base

**Success Criteria:** File uploaded successfully, version history updated

### Flow Diagram

```mermaid
graph TD
    Start([User navigates to Knowledge Base]) --> View[See current versions]
    View --> Choose{Which file?}
    Choose -->|Good List| GL[Click Upload Good List]
    Choose -->|EXIM Tariff| Tariff[Click Upload EXIM Tariff]

    GL --> SelectGL[Select .xls/.xlsx file]
    Tariff --> SelectTariff[Select .xls/.xlsx file]

    SelectGL --> ValidateGL{Valid format?}
    SelectTariff --> ValidateTariff{Valid format?}

    ValidateGL -->|No| ErrorGL[Show error: Invalid format or missing columns]
    ValidateTariff -->|No| ErrorTariff[Show error: Invalid format]
    ErrorGL --> SelectGL
    ErrorTariff --> SelectTariff

    ValidateGL -->|Yes| PreviewGL[Show preview: first 10 rows, total count]
    ValidateTariff -->|Yes| PreviewTariff[Show preview: first 10 rows, total count]

    PreviewGL --> ConfirmGL[Confirm: Replace 1,294 entries?]
    PreviewTariff --> ConfirmTariff[Confirm: Replace entries?]

    ConfirmGL --> ImportGL[Background import via Celery]
    ConfirmTariff --> ImportTariff[Background import via Celery]

    ImportGL --> StatusGL{Import status}
    ImportTariff --> StatusTariff{Import status}

    StatusGL -->|Success| SuccessGL[Show: 1,532 entries imported]
    StatusTariff -->|Success| SuccessTariff[Show: Tariff updated]

    StatusGL -->|Failed| FailGL[Show specific error, allow retry]
    StatusTariff -->|Failed| FailTariff[Show specific error, allow retry]

    SuccessGL --> Updated([Version history updated])
    SuccessTariff --> Updated
```

### Edge Cases & Error Handling

- **File too large (>2MB):** Reject with message "File too large. Maximum 2MB. Consider removing unnecessary columns."
- **Missing required columns:** Specific error "Missing column: hs_code. Please check template."
- **Import timeout (large file):** Show progress indicator "Processing large file... 45% complete"
- **Duplicate entries:** Preview shows warning "47 duplicate HS codes detected. All variations will be kept for fuzzy matching."

**Notes:**
- Versioning prevents accidental data loss
- Preview step is critical for confidence
- Operations managers use this monthly

---
