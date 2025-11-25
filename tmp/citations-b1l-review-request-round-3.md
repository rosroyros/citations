You are conducting a code review.

## Task Context

### Beads Issue ID: citations-b1l

citations-b1l: Auto-scroll to validation results on submission
Status: closed
Priority: P2
Type: feature
Created: 2025-11-21 06:38
Updated: 2025-11-24 10:45

Description:
After submitting citations, user must manually scroll down to see validation results/loading states.

## Requirements
- Auto-scroll to validation table when user clicks "Check Citations"
- Smooth scroll animation (not instant jump)
- Scroll to top of validation loading state/results section
- Consider mobile viewport (ensure results visible)

### What Was Implemented

ROUND 3 - URGENT: Auto-scroll functionality NOT working in browser despite passing tests.

Current implementation:
- ✅ Uses React useEffect with ref to target validation section
- ✅ Attempts scrollIntoView with smooth behavior
- ✅ Has 100ms delay for DOM readiness
- ✅ Includes accessibility support with prefers-reduced-motion
- ✅ Added fallback manual scroll using window.scrollTo
- ✅ Added extensive debug logging
- ✅ Playwright tests pass (but may be testing wrong thing)

**CRITICAL ISSUE**: Despite implementation looking correct and tests passing, auto-scroll does NOT work in actual browser testing. Users report no scrolling behavior when clicking "Check Citations".

**Current Debug Approach**: Added console logging and fallback scroll method, but need expert guidance on root cause.

### Requirements/Plan

Key requirements from task description:
- Auto-scroll to validation table when user clicks "Check Citations"
- Smooth scroll animation (not instant jump)
- Scroll to top of validation loading state/results section
- Consider mobile viewport (ensure results visible)

**ROUND 1 & 2 FEEDBACK ADDRESSED:**
- ✅ Fixed page refresh recovery auto-scroll
- ✅ Added test for rapid state changes edge case
- ✅ Replaced magic number with SCROLL_CONFIG.DELAY_MS constant
- ✅ Added prefers-reduced-motion accessibility support
- ✅ Added optional chaining for browser compatibility

**ROUND 3 CRITICAL ISSUE:** Auto-scroll not working in real browser despite correct-looking code.

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 19226dfb0e80457786778e9b27200029a75565ed
- HEAD_SHA: bd5535bff72987a95526fdf6eea8baf15c90a3eb

Key code section needing review (App.jsx lines 61-102):
```javascript
// Auto-scroll to validation results when loading starts
useEffect(() => {
  if (loading && submittedText && validationSectionRef.current) {
    const scrollTimer = setTimeout(() => {
      // Debug logging
      console.log('Auto-scroll: validationSectionRef.current:', validationSectionRef.current)
      console.log('Auto-scroll: Element bounding rect:', validationSectionRef.current.getBoundingClientRect())

      const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false

      // Try both scrollIntoView and manual scroll as fallback
      try {
        validationSectionRef.current.scrollIntoView({
          behavior: prefersReducedMotion ? 'auto' : 'smooth',
          block: 'start',
          inline: 'nearest'
        })

        // Fallback: manual scroll to element position
        setTimeout(() => {
          const elementTop = validationSectionRef.current.getBoundingClientRect().top + window.scrollY
          const headerOffset = 100
          const scrollTo = elementTop - headerOffset

          console.log('Auto-scroll fallback: scrolling to position:', scrollTo)
          window.scrollTo({
            top: scrollTo,
            behavior: prefersReducedMotion ? 'auto' : 'smooth'
          })
        }, 100)
      } catch (error) {
        console.error('Auto-scroll error:', error)
      }
    }, SCROLL_CONFIG.DELAY_MS)

    return () => clearTimeout(scrollTimer)
  }
}, [loading, submittedText])
```

## Specific Questions for Reviewer

**PLEASE PROVIDE SPECIFIC GUIDANCE ON:**

1. **Why does scrollIntoView not work despite correct implementation?**
   - Element exists (ref is set)
   - useEffect triggers correctly
   - Delay allows DOM to render

2. **What could prevent scrollIntoView from working?**
   - CSS issues (overflow, position, etc.)
   - Timing/rendering issues
   - Browser-specific problems
   - React rendering conflicts

3. **How to debug this systematically?**
   - What specific console logs should we add?
   - What DOM properties should we check?
   - How to verify the scroll is actually called?

4. **Is there a better approach than scrollIntoView?**
   - Manual scroll calculation?
   - Different React patterns?
   - CSS-based solutions?

## Review Criteria

**CRITICAL FOCUS**: Please help identify why auto-scroll isn't working in real browser despite correct-looking code and passing tests.

**Adherence to Task:**
- Does current implementation have fundamental issues?
- What specific changes are needed to make auto-scroll actually work?

**Code Quality:**
- Are there obvious bugs in the scroll logic?
- Are we using the right approach for React?

**Testing:**
- Are current tests giving false positives?
- How to write tests that verify actual scrolling behavior?

## Required Output Format

**URGENT REQUEST**: Please provide specific, actionable guidance on:
1. Root cause analysis of why scrollIntoView isn't working
2. Specific code changes needed to fix auto-scroll
3. Better debugging approach if needed
4. Alternative implementation approaches if scrollIntoView is fundamentally flawed

Be specific with file:line references and concrete code suggestions.