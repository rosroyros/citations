# Audit Summary: 94 Remaining Citations

**Date**: 2025-11-11
**Task**: Audit citations that GPT-5-mini got CORRECT to verify ground truth

---

## 📊 Overview

Total citations audited: **94**
- Model predicted these correctly
- Need to verify ground truth labels are accurate

## 🔍 Automated Audit Results

The automated audit flagged **46 citations (48.9%)** as potential ground truth errors:

### Breakdown by Verdict:
- **35 citations**: GT says INVALID but should be VALID
- **11 citations**: GT says VALID but should be INVALID

### Breakdown by Provenance:
- **6 Manual/Original** - Errors in original curation
- **37 Synthetic (with seed)** - Can compare to original
- **3 Synthetic (no seed)** - Seed not found

## ⚠️ Important Caveats

The automated audit has **known limitations**:
- Cannot distinguish journal names (title case) from article titles (sentence case)
- Cannot verify italic formatting in plain text
- May over-flag title case issues
- Cannot apply context-specific APA rules

**The automated findings are a STARTING POINT, not final judgments.**

## 📁 Files Generated

### Main Audit Files:
1. **REMAINING_94_TO_AUDIT.jsonl** - The 94 citations to audit
2. **AUDIT_PENDING_94.json** - Automated audit results (all 94)
3. **AUDIT_WORKSHEET.md** - Full worksheet with automated findings

### Provenance Files:
4. **PROVENANCE_94_REMAINING.json** - Provenance for all 94 citations
5. **PROVENANCE_94_REMAINING_READABLE.md** - Human-readable provenance
6. **FLAGGED_CITATIONS_PROVENANCE.json** - Provenance for 46 flagged citations
7. **FLAGGED_CITATIONS_PROVENANCE.md** - Human-readable flagged citations report ⭐

### This File:
8. **AUDIT_SUMMARY.md** - This summary document

## 🎯 Recommended Next Steps

1. **Review the 46 flagged citations** using `FLAGGED_CITATIONS_PROVENANCE.md`
   - Each citation shows: seed vs synthetic, automated findings, metadata
   - Use https://libguides.css.edu/APA7thEd/ as reference

2. **Focus on these categories first:**
   - **6 Manual/Original flagged** - These are errors in original curation
   - **Citations with clear provenance** - Can see what was changed

3. **Mark your decisions** for each flagged citation:
   - GT_CORRECT - Ground truth is accurate
   - GT_ERROR_SHOULD_BE_VALID - Should be marked VALID
   - GT_ERROR_SHOULD_BE_INVALID - Should be marked INVALID

4. **Consolidate findings** into ground truth corrections file

## 📖 Key Examples

### Citation #4 - Synthetic with Obvious Error
- **GT**: INVALID
- **Automated**: Should be VALID (wrong!)
- **Seed**: "International Organization for Standardization"
- **Synthetic**: "I. O. for Standardization" ← ABBREVIATION ERROR
- **Verdict**: GT is CORRECT (INVALID) - abbreviated author name

### Citation #6 - Synthetic with Date Format Error  
- **GT**: INVALID
- **Automated**: Should be VALID (wrong!)
- **Seed**: "(2016, July 3)" with comma
- **Synthetic**: "(2016 July 3)" without comma ← MISSING COMMA
- **Verdict**: GT is CORRECT (INVALID) - date format error

### Citation #15 - Journal Name (False Flag)
- **GT**: VALID
- **Automated**: Should be INVALID (wrong!)
- **Issue**: "Kairos: A Journal of Rhetoric, Technology, and Pedagogy"
- **Verdict**: GT is CORRECT (VALID) - this IS the journal name, title case is correct

## 🔢 Expected Error Rate

Based on previous 27-citation audit:
- Found 9 GT errors out of 27 (33% error rate)
- Extrapolating: expect ~31 GT errors in these 94 citations
- But automated audit flagged 46 (likely many false positives)

## 📝 Notes

- En-dash vs hyphen differences were IGNORED per task instructions
- Journal names use title case (different from article titles)
- Some automated flags are false positives due to context limitations
- Manual human review is essential for final decisions

---

**Status**: Automated audit complete, ready for manual review
**Primary File for Review**: `FLAGGED_CITATIONS_PROVENANCE.md`
