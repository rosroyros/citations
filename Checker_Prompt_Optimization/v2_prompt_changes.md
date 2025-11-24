# V2 Prompt Changes

## Summary
Added 4 principle-based rules to validator_prompt_optimized.txt

## File Created
- backend/prompts/validator_prompt_v2.txt

## Changes Made
1. Principle 1: Format Flexibility (~35 lines)
   - Addresses 8 error patterns (DOI formats, classical works, international, article numbers)

2. Principle 2: Source-Type Specific Requirements (~25 lines)
   - Addresses 4 error patterns (retrieval dates, government pubs, series, editions)

3. Principle 3: Strict Ordering and Punctuation (~20 lines)
   - Addresses 3 error patterns (dissertation numbers, URL punctuation, journal formatting)

4. Principle 4: Location Specificity (~10 lines)
   - Addresses 1 error pattern (conference locations)

## Total Addition
- ~102 new lines of principles
- Original: 74 lines
- V2: 176 lines
- Net increase: 102 lines

## Error Patterns Addressed
- 16 false positive patterns (model too strict)
- 5 false negative patterns (model too lenient)
- Total: All 21 error patterns from analysis

## No Examples Added
- Used principle-based rules only
- No few-shot examples from test set
- Avoids test set contamination

## Principles Added

### Principle 1: Format Flexibility
- DOI format variations (doi: vs https://doi.org/)
- Complex DOI suffixes
- Classical work date ranges
- International publisher names and domains
- Journal abbreviations in any language
- Extended bracketed descriptions
- Article numbers (correct format, not errors)

### Principle 2: Source-Type Specific Requirements
- Retrieval dates for dynamic sources
- Government publication hierarchies
- Book series formatting
- Edition abbreviations (ed., Rev. ed., etc.)

### Principle 3: Strict Ordering and Punctuation
- Dissertation publication number placement
- URL punctuation rules
- Journal volume/issue formatting

### Principle 4: Location Specificity
- Full state names in conference locations

## Integration Details
- Inserted after existing source-type instructions
- Positioned before "OUTPUT FORMAT" section
- Maintains existing markdown formatting style
- Preserves all original functionality