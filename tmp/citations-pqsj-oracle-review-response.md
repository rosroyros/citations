Now let me compile the code review. I've found several critical security issues and other important problems.

## Code Review: Citations Accessibility Enhancement (citations-pqsj)

### 1. **Critical Issues** ❌

#### **CRITICAL: XSS Vulnerability in formatCitations function**
**Location:** `dashboard/static/index.html:1439, 1443, 1446, 1449, 1453`

**Issue:** The `formatCitations` function directly interpolates unsanitized user input (`trimmed`, `previewText`, `fullText`) into HTML without escaping. This creates multiple XSS attack vectors where malicious citation text could execute JavaScript.

**Attack Example:**
```javascript
// If validation.citations contains:
"PREVIEW: <img src=x onerror=alert('XSS')>"
// This will execute JavaScript when rendered
```

**Current Code:**
```javascript
return `<div class="citation-item" role="listitem" aria-label="Preview citation ${index + 1}">📋 <span class="citation-text">${previewText}</span></div>`
```

**Impact:** High - Allows arbitrary JavaScript execution in user's browser, potential data theft, session hijacking.

**Fix Required:** HTML-escape all user-provided text before interpolation:
```javascript
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
// Then use: ${escapeHtml(previewText)}
```

---

#### **CRITICAL: XSS in aria-label attributes**
**Location:** `dashboard/static/index.html:1439, 1443, 1453`

**Issue:** User-controlled text is directly interpolated into `aria-label` attributes without escaping quotes, allowing attribute injection attacks.

**Attack Example:**
```javascript
// If citation contains:
'test" onclick="alert(\'XSS\')" data-x="'
// Results in:
aria-label="Citation 1: test" onclick="alert('XSS')" data-x=""
```

**Fix Required:** Escape quotes in aria-label attributes or use `setAttribute()` instead of template literals.

---

#### **CRITICAL: Invalid CSS property in stylesheet**
**Location:** `dashboard/static/index.html:784`

**Issue:** `tabindex: 0;` is written as a CSS property, but `tabindex` is an HTML attribute, not a CSS property. This has no effect and breaks the keyboard navigation requirement.

**Current Code:**
```css
.citations-text {
    /* Accessibility improvements */
    tabindex: 0;  /* ❌ This does nothing! */
    outline: none;
}
```

**Impact:** Keyboard navigation completely broken for citations containers that don't have the HTML attribute set. This violates WCAG 2.1 AA requirements.

**Fix:** Remove from CSS (line 784). The HTML already correctly has `tabindex="0"` attribute (line 1355).

---

### 2. **Important Issues** ⚠️

#### **IMPORTANT: Duplicate aria-live regions cause screen reader spam**
**Location:** `dashboard/static/index.html:1411, 1416, 1423, 1428, 1446, 1449`

**Issue:** Every citation item with error/warning gets `aria-live="assertive"` or `aria-live="polite"`. When rendering 20 citations, screen readers announce each one separately, creating noise pollution.

**Impact:** Poor screen reader UX - users are bombarded with announcements. Violates WCAG 2.1 SC 4.1.3 (Status Messages).

**Fix:** Only the container should have `aria-live`, not individual items. Remove `aria-live` from line 1411, 1416, 1423, 1428, 1446, 1449.

---

#### **IMPORTANT: Missing role="list" wrapper**
**Location:** `dashboard/static/index.html:1456`

**Issue:** Individual citations have `role="listitem"` but are not wrapped in a `role="list"` container. This breaks screen reader list navigation.

**Current Structure:**
```html
<div role="region">
  <div role="listitem">Citation 1</div>  ❌ Invalid - listitem without list
  <div role="listitem">Citation 2</div>
</div>
```

**Fix Required:** Wrap all citation items in a container with `role="list"`:
```javascript
const citationsHtml = lines.map(...).filter(...).join('');
return `<div role="list">${citationsHtml}</div>`;
```

---

#### **IMPORTANT: Keyboard event handler memory leak**
**Location:** `dashboard/static/index.html:1464-1509`

**Issue:** `setupCitationsKeyboardNavigation` adds event listeners but never removes them. When job details are closed and reopened, multiple listeners accumulate on the same element.

**Fix Required:** Remove existing listeners before adding new ones, or use event delegation.

---

#### **IMPORTANT: Missing HTML escaping in announceToScreenReader**
**Location:** `dashboard/static/index.html:1518`

**Issue:** While the current usage only passes static strings ('Scrolled down', etc.), the function accepts arbitrary `message` parameter which is set via `textContent`. If future code passes user input here, it could be vulnerable.

**Current Code:**
```javascript
announcement.textContent = message;  // ✅ Safe for now
```

**Recommendation:** Add documentation that this function must only receive trusted strings, or add input validation.

---

#### **IMPORTANT: Inconsistent touch target implementation**
**Location:** `dashboard/static/index.html:827-829`

**Issue:** Copy button uses `min-height: 44px; min-width: 44px;` but the actual rendered size may be smaller due to padding/borders not being included in these calculations. WCAG 2.1 SC 2.5.5 requires 44×44px **target size**, not just minimum dimensions.

**Fix:** Test actual rendered dimensions or use explicit `width: 44px; height: 44px;` with `box-sizing: border-box`.

---

#### **IMPORTANT: Missing requirement - formatCitations doesn't match task description**
**Location:** `dashboard/static/index.html:1456`

**Issue:** Task description states "Smart citation formatting for PREVIEW/FULL citation types with appropriate icons" and "APA citation parsing and categorization (journals, books, websites)". 

The implementation shows icons for PREVIEW/FULL but does **not** parse or categorize APA citations by type (journal vs book vs website). All regular citations are formatted identically.

**Fix:** Either implement APA categorization or update task description to reflect actual implementation.

---

### 3. **Minor Issues** 💡

#### **MINOR: Redundant trimming**
**Location:** `dashboard/static/index.html:1450`

```javascript
} else if (trimmed.trim()) {  // trimmed is already trimmed!
```

**Fix:** Change to `} else if (trimmed) {`

---

#### **MINOR: Inefficient string concatenation**
**Location:** `dashboard/static/index.html:1456`

**Issue:** Using `join('')` on HTML strings is less efficient than building a proper DOM structure, especially for large citation lists.

**Recommendation:** For performance, consider using `DocumentFragment` or innerHTML once instead of string concatenation.

---

#### **MINOR: Magic number in keyboard navigation**
**Location:** `dashboard/static/index.html:1468, 1473`

```javascript
citationsText.scrollTop += 50;  // Why 50px?
```

**Recommendation:** Use CSS variable or calculate based on line-height for consistent scrolling.

---

#### **MINOR: Missing screen reader context for copy action**
**Location:** `dashboard/static/index.html:1469, 1474, etc.**

**Issue:** Screen reader announces "Scrolled down" but doesn't indicate current position (e.g., "Scrolled down, showing citations 5-10 of 20").

**Recommendation:** Enhance announcements with scroll position context.

---

#### **MINOR: Announcement element not removed on error**
**Location:** `dashboard/static/index.html:1523-1525`

**Issue:** If `setTimeout` callback throws or if page navigates quickly, announcement elements may leak into DOM.

**Fix:** Use try-finally or store references to clean up.

---

#### **MINOR: Accessibility test file not integrated**
**Location:** `dashboard/test_citations_accessibility.html`

**Issue:** Test file exists but is not mentioned in commit or integrated into CI/CD. Tests appear to be manual only.

**Recommendation:** Integrate into automated test suite or document manual testing procedure.

---

### 4. **Strengths** ✅

1. **Comprehensive keyboard navigation** - Arrow keys, Page Up/Down, Home/End support is well-implemented
2. **Proper ARIA roles and labels** - Good use of `role="region"`, `aria-label`, `aria-describedby`
3. **Touch target awareness** - Attempted to meet 44px WCAG requirement (though implementation needs verification)
4. **Screen reader helper function** - Good pattern with `announceToScreenReader()` for dynamic announcements
5. **Loading and error states** - Semantic handling of different citation states with appropriate ARIA attributes
6. **CSS variables for magic numbers** - Good use of `--citations-max-height` and `--citations-mobile-max-height`
7. **High contrast mode consideration** - CSS media query for `prefers-contrast: high`
8. **Comprehensive test coverage** - Test file covers 6 accessibility categories
9. **Focus management** - Enhanced focus indicators with outline and box-shadow
10. **Mobile-responsive design** - Separate max-height for mobile viewports

---

## Summary

**Status: 🔴 MUST NOT MERGE - Critical security vulnerabilities**

**Critical Issues:** 3 (XSS vulnerability, XSS in aria-labels, broken keyboard navigation)
**Important Issues:** 6 (aria-live spam, invalid ARIA structure, memory leak, touch targets, missing APA parsing)
**Minor Issues:** 6 (code style, performance, UX polish)

**Primary Concerns:**
1. **XSS vulnerability** in formatCitations must be fixed immediately - this is a security vulnerability that allows arbitrary code execution
2. **Invalid CSS** breaks keyboard navigation requirement - core accessibility feature is non-functional
3. **ARIA structure violations** - listitem without list, duplicate aria-live regions

**Recommendations:**
1. Fix all Critical issues before any deployment
2. Add HTML sanitization/escaping utility function
3. Run actual screen reader tests (NVDA/JAWS) to verify announcements
4. Add automated security scanning for XSS in CI/CD
5. Verify touch target compliance with actual measurements on mobile devices
