# 🚀 DEV AGENT HANDOFF - Story 1.7.1 Implementation

**Date:** 2025-10-27
**From:** John (Product Manager)
**To:** Dev Agent
**Priority:** HIGH (Blocks Story 1.7 QA Approval)

---

## 📋 What's Done

✅ **Sprint Change Proposal Approved** - Story 1.7.1 rescoped from CD.xlsx extraction to expected-results.json validation

✅ **New Validation Script Created** - `backend/validate_extraction_results.py` (685 lines)
- Loads expected-results.json (camelCase schema)
- Loads results.json (snake_case schema)
- Compares fields with fuzzy/numeric/exact matching
- Generates visual markdown reports

✅ **Old Script Archived** - `backend/validate_sample.py` → `backend/validate_sample_cd_xlsx.py`

✅ **Initial Test Complete** - Sample 1 validated successfully
- Report: `resources/sample/1/validation-report-20251027-005840.md`
- Results: 29.3% accuracy (53 PASS, 128 MISSING, 191 EXTRA)

---

## 🎯 What You Need to Do

### **PRIORITY 1: Fix Field Mapping (CRITICAL)**

**Problem:** 70.7% of fields marked as MISSING due to schema mismatch

**Root Cause:**
- `expected-results.json` has deeply nested structure: `declarationHeader.importer.code`
- `results.json` has flat structure: `importer.tax_code`
- Current FIELD_MAPPING doesn't handle nested paths correctly

**Your Task:**
1. Review Sample 1 report: `resources/sample/1/validation-report-20251027-005840.md`
2. Identify common missing field patterns (all under `declarationHeader.*`)
3. Enhance `validate_extraction_results.py`:
   - Option A: Flatten expected-results.json structure before comparison
   - Option B: Update FIELD_MAPPING to map nested → flat paths correctly
   - **Recommended: Option A** (simpler, more maintainable)
4. Re-run validation on Sample 1
5. **Success criteria**: Reduce MISSING fields from 128 to <30

**Files to Edit:**
- `backend/validate_extraction_results.py` (lines 50-150: FIELD_MAPPING section)
- Specifically: Update `flatten_dict()` function or FIELD_MAPPING entries

---

### **PRIORITY 2: Validate All 3 Samples**

**Your Task:**
```bash
cd backend
python3 validate_extraction_results.py ../resources/sample/1  # Re-test after mapping fix
python3 validate_extraction_results.py ../resources/sample/2
python3 validate_extraction_results.py ../resources/sample/3
```

**Expected Output:**
- 3 validation reports generated
- Accuracy >70% for each sample (after mapping fix)
- Clear visual reports showing ✅ PASS / ❌ FAIL / 🔴 MISSING

**Deliverable:** All 3 validation reports in respective sample folders

---

### **PRIORITY 3: Update Integration Tests**

**File:** `backend/tests/integration/test_end_to_end_processing.py`

**Changes Needed:**

1. **Line 30** - Update path:
```python
# OLD
VALIDATION_REFERENCE_PATH = ... / "validation-reference.json"

# NEW (per-sample files)
SAMPLE_FILES_BASE = Path(...) / "resources" / "sample"
```

2. **Lines 34-50** - Update load function:
```python
# OLD
def load_validation_reference() -> Dict[str, Any]:
    with open(VALIDATION_REFERENCE_PATH, 'r') as f:
        return json.load(f)

# NEW
def load_expected_results(sample_number: int) -> Dict[str, Any]:
    expected_path = SAMPLE_FILES_BASE / str(sample_number) / "expected-results.json"
    with open(expected_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # expected-results.json is an array, extract first element
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return data
```

3. **Throughout file** - Update validation calls to use new function

4. **Test:** `pytest backend/tests/integration/test_end_to_end_processing.py -v`

---

### **PRIORITY 4: Update Story 1.7 References**

**File:** `docs/stories/1.7.end-to-end-processing.md`

**Changes:**

1. **Task 8** (around line 273):
```markdown
# OLD
- [ ] Create manual validation reference file: `resources/sample/validation-reference.json`

# NEW
- [x] Validation reference files created: `resources/sample/{1,2,3}/expected-results.json`
- [x] **SOURCE:** expected-results.json files are manually curated ground truth
- [ ] Validation tool: Use `backend/validate_extraction_results.py`
- [ ] Run validation for all 3 samples and review markdown reports
```

2. **QA Results Section** (around line 1014):
```markdown
# OLD
### 2. **BLOCKER**: Missing Validation Reference

# NEW
### 2. **RESOLVED**: Validation Reference Created
**Status**: ✅ RESOLVED - User manually created expected-results.json
See Story 1.7.1 Sprint Change Proposal (2025-10-27)
```

---

### **PRIORITY 5: Create Validation Guide**

**File:** `docs/qa/validation-guide.md` (NEW)

**Content:** See Sprint Change Proposal for full template

**Key Sections:**
- Overview of validation workflow
- File structure (expected-results.json vs results.json)
- Running validation command
- Interpreting validation reports (status indicators)
- Schema translation explanation
- Troubleshooting guide

**Reference:** Validation report example at `resources/sample/1/validation-report-20251027-005840.md`

---

## 📁 Files Modified So Far

**Created:**
- ✅ `backend/validate_extraction_results.py` (685 lines)
- ✅ `docs/stories/1.7.1-validation-against-expected-results.md` (new story version)
- ✅ `resources/sample/1/validation-report-20251027-005840.md` (test output)

**Modified:**
- ✅ `backend/validate_sample_cd_xlsx.py` (renamed + archive notice added)

**Backed Up:**
- ✅ `docs/stories/1.7.1-comprehensive-validation-reference.md.backup` (original version)

---

## 🎯 Success Criteria

Before marking Story 1.7.1 as DONE:

- [ ] Field mapping fixed - <30 MISSING fields per sample
- [ ] All 3 samples validated successfully
- [ ] Validation reports generated with >70% accuracy
- [ ] Integration tests updated and passing
- [ ] Story 1.7 references updated
- [ ] Validation guide documentation complete
- [ ] Visual reports clearly show ✅/❌/🔴 status for each field

---

## 🔍 Key Files for Reference

**Story Documents:**
- **CURRENT:** `docs/stories/1.7.1-validation-against-expected-results.md` (USE THIS ONE - v2.2 with all fixes)
- Old (backup): `docs/stories/1.7.1-comprehensive-validation-reference.md.backup` (deprecated - CD.xlsx approach)
- Related: `docs/stories/1.7.end-to-end-processing.md`

**Code:**
- New validation: `backend/validate_extraction_results.py`
- Archived: `backend/validate_sample_cd_xlsx.py`
- Integration tests: `backend/tests/integration/test_end_to_end_processing.py`

**Data:**
- Ground truth: `resources/sample/{1,2,3}/expected-results.json`
- LLM output: `resources/sample/{1,2,3}/results.json`
- Reports: `resources/sample/{1,2,3}/validation-report-*.md`

---

## 💡 Implementation Tips

### Field Mapping Fix (Priority 1)

The issue is that `expected-results.json` wraps everything under `declarationHeader`, but `results.json` doesn't.

**Quick Fix Approach:**
```python
def flatten_expected_results(data: dict) -> dict:
    """Flatten declarationHeader wrapper if present"""
    if "declarationHeader" in data:
        # Extract contents of declarationHeader to root level
        header_data = data["declarationHeader"]
        # Move nested fields up one level
        return header_data
    return data
```

Call this in `load_expected_results()` before returning.

### Testing Your Changes

After field mapping fix:
```bash
# Test Sample 1 again
python3 validate_extraction_results.py ../resources/sample/1

# Check the new report
cat ../resources/sample/1/validation-report-*.md | head -50

# Should see significantly fewer MISSING fields
```

---

## 📞 Questions?

If you have questions about:
- **Expected behavior**: Check `docs/stories/1.7.1-validation-against-expected-results.md`
- **Sprint change context**: See Context section in story file
- **Field mapping**: Review FIELD_MAPPING in `validate_extraction_results.py` lines 50-150
- **Report format**: See `resources/sample/1/validation-report-20251027-005840.md`

---

## ✅ Handoff Checklist

- [x] Sprint Change Proposal approved by user
- [x] New validation script created and tested
- [x] Old script archived
- [x] Story document updated
- [x] Initial test run complete (Sample 1)
- [x] Handoff document created
- [ ] **→ Ready for dev agent implementation**

---

**Good luck! The foundation is solid - just need to fix the field mapping and complete the remaining priorities.** 🚀
