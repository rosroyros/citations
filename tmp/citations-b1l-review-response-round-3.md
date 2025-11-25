The root cause is **CSS overflow conflicts preventing `scrollIntoView` from working**. The tests give false positives because they check scroll position changes, not actual element visibility. 

**Fix**: Add CSS overflow reset for `html/body` and replace `scrollIntoView` with manual scroll calculation using `getBoundingClientRect()` + `window.scrollTo()`.
