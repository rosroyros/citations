You are conducting a code review.

## Task Context

### Beads Issue ID: etxk

citations-etxk: P3.5: Add conversion funnel chart to dashboard
Status: in_progress
Priority: P1
Type: task
Created: 2025-12-10 22:11
Updated: 2025-12-11 20:25

Description:

## Overview

Add Conversion Funnel Chart to the dashboard's static HTML to visualize A/B test performance.

**Files to modify:**
- `dashboard/static/index.html` - Add chart HTML and JavaScript
- `backend/app.py` - Add `/api/funnel-data` endpoint

**Why this is needed:** Users need to SEE which pricing variant (Credits vs Passes) converts better. A funnel chart shows the drop-off at each stage: Pricing Shown → Selected → Checkout → Purchase. Without visual comparison, it's hard to determine the winner.

**Oracle Feedback #5:** We track `experiment_variant` on all events, so we can create side-by-side funnels for variant 1 vs variant 2.

## Important Context

**What is a conversion funnel chart?**

A visual representation showing how many users progress through each stage of the upgrade flow, with drop-offs visible at each step:

```
Variant 1 (Credits)           Variant 2 (Passes)
┌─────────────┐               ┌─────────────┐
│   Shown     │ 150           │   Shown     │ 155
└──────┬──────┘               └──────┬──────┘
       │ 30%                          │ 34%
┌──────┴──────┐               ┌──────┴──────┐
│  Selected   │ 45            │  Selected   │ 52
└──────┬──────┘               └──────┬──────┘
       │ 89%                          │ 92%
┌──────┴──────┐               ┌──────┴──────┐
│  Checkout   │ 40            │  Checkout   │ 48
└──────┬──────┘               └──────┬──────┘
       │ 80%                          │ 83%
┌──────┴──────┐               ┌──────┴──────┐
│  Purchase   │ 32            │  Purchase   │ 40
└─────────────┘               └─────────────┘
```

**Chart Type:** Horizontal bar chart with grouped bars (variant 1 and variant 2 side-by-side for each stage)

**Data Source:** `/api/funnel-data` endpoint calls `parse_upgrade_events()` from P3.4

### What Was Implemented

Added a funnel chart to the dashboard that visualizes A/B test performance between Credits (Variant 1) and Passes (Variant 2) pricing models. The implementation includes:
1. A new `/api/funnel-data` endpoint in `backend/app.py` that parses upgrade events using analytics.py
2. HTML for the funnel chart in `dashboard/static/index.html` with proper styling
3. JavaScript code that creates a horizontal bar chart showing 4 funnel stages
4. Integration with the existing date range filter to refresh the chart

### Requirements/Plan

**Complete Implementation**

### Part 1: Add API Endpoint (backend/app.py)

Add this endpoint to `backend/app.py` after the existing dashboard routes:

```python
@app.get("/api/funnel-data")
async def get_funnel_data(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    variant: Optional[str] = None
):
```

### Part 2: Add Chart HTML (dashboard/static/index.html)

Find the section with existing charts (around line 1410, look for `<div class="charts-section">`).

Add this new chart container AFTER the existing charts (after the providerChart div):

```html
<!-- Conversion Funnel Chart (A/B Test) -->
<div class="chart-container glass-card" style="padding: var(--space-xl);">
    <div class="chart-header" style="margin-bottom: var(--space-lg);">
        <h3 style="color: var(--color-text-primary); font-weight: 600; font-size: 18px; margin: 0;">
            Upgrade Funnel - A/B Test Comparison
        </h3>
        <p style="color: var(--color-text-tertiary); font-size: 13px; margin: 4px 0 0 0;">
            Credits (Variant 1) vs Passes (Variant 2)
        </p>
    </div>
    <div style="position: relative; height: 400px;">
        <canvas id="funnelChart"></canvas>
    </div>
    <!-- Summary stats below chart -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-lg); margin-top: var(--space-xl); padding-top: var(--space-lg); border-top: 1px solid var(--color-border);">
        <div>
            <div style="font-size: 12px; color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Variant 1 (Credits)</div>
            <div style="font-size: 24px; font-weight: 700; color: var(--color-text-primary);" id="variant1-conversion">-</div>
            <div style="font-size: 13px; color: var(--color-text-secondary);" id="variant1-count">- purchases</div>
        </div>
        <div>
            <div style="font-size: 12px; color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Variant 2 (Passes)</div>
            <div style="font-size: 24px; font-weight: 700; color: var(--color-text-primary);" id="variant2-conversion">-</div>
            <div style="font-size: 13px; color: var(--color-text-secondary);" id="variant2-count">- purchases</div>
        </div>
    </div>
</div>
```

### Part 3: Add Chart JavaScript (dashboard/static/index.html)

Find the JavaScript section where existing charts are initialized (look for `validationsChart = new Chart`, around line 2260).

Add this code AFTER the existing chart initialization:

```javascript
// Funnel Chart - A/B Test Comparison
let funnelChart = null;

async function loadFunnelChart() {
    const ctx = document.getElementById('funnelChart');
    if (!ctx) {
        console.error('Funnel chart canvas not found');
        return;
    }

    try {
        // Get current date range filter
        const dateRange = document.getElementById('date-range-filter')?.value || '7d';

        // Calculate from_date based on range
        let from_date = '';
        if (dateRange !== 'all') {
            const now = new Date();
            const days = parseInt(dateRange.replace('d', ''));
            const fromDate = new Date(now.getTime() - (days * 24 * 60 * 60 * 1000));
            from_date = fromDate.toISOString().split('T')[0]; // YYYY-MM-DD
        }

        // Fetch funnel data
        const url = from_date ? `/api/funnel-data?from_date=${from_date}` : '/api/funnel-data';
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Failed to load funnel data: ${response.status}`);
        }

        const data = await response.json();

        // Extract counts for each stage
        const labels = ['Pricing Shown', 'Product Selected', 'Checkout Started', 'Purchase Completed'];

        const variant1Data = [
            data.variant_1.pricing_table_shown,
            data.variant_1.product_selected,
            data.variant_1.checkout_started,
            data.variant_1.purchase_completed
        ];

        const variant2Data = [
            data.variant_2.pricing_table_shown,
            data.variant_2.product_selected,
            data.variant_2.checkout_started,
            data.variant_2.purchase_completed
        ];

        // Update summary stats
        const v1Rate = (data.conversion_rates.variant_1.overall * 100).toFixed(1);
        const v2Rate = (data.conversion_rates.variant_2.overall * 100).toFixed(1);

        document.getElementById('variant1-conversion').textContent = `${v1Rate}%`;
        document.getElementById('variant1-count').textContent = `${data.variant_1.purchase_completed} purchases`;

        document.getElementById('variant2-conversion').textContent = `${v2Rate}%`;
        document.getElementById('variant2-count').textContent = `${data.variant_2.purchase_completed} purchases`;

        // Destroy existing chart if it exists
        if (funnelChart) {
            funnelChart.destroy();
        }

        // Create new chart
        funnelChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Variant 1 (Credits)',
                        data: variant1Data,
                        backgroundColor: 'rgba(147, 51, 234, 0.8)', // Brand purple
                        borderColor: 'rgba(147, 51, 234, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Variant 2 (Passes)',
                        data: variant2Data,
                        backgroundColor: 'rgba(59, 130, 246, 0.8)', // Blue
                        borderColor: 'rgba(59, 130, 246, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                indexAxis: 'y', // Horizontal bars
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: {
                                family: 'Work Sans',
                                size: 13
                            },
                            color: '#4a5568',
                            padding: 16
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.x;
                                const stage = context.label;

                                // Calculate percentage drop from previous stage
                                const dataIndex = context.dataIndex;
                                if (dataIndex > 0) {
                                    const prevValue = context.dataset.data[dataIndex - 1];
                                    const retention = prevValue > 0 ? ((value / prevValue) * 100).toFixed(1) : 0;
                                    return `${label}: ${value} (${retention}% retention)`;
                                }

                                return `${label}: ${value}`;
                            }
                        },
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: {
                            family: 'Work Sans',
                            size: 13
                        },
                        bodyFont: {
                            family: 'Work Sans',
                            size: 12
                        },
                        padding: 12
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Users',
                            font: {
                                family: 'Work Sans',
                                size: 12
                            },
                            color: '#718096'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            font: {
                                family: 'Work Sans',
                                size: 11
                            },
                            color: '#718096'
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                family: 'Work Sans',
                                size: 12
                            },
                            color: '#4a5568'
                        }
                    }
                }
            }
        });

        console.log('Funnel chart loaded successfully');

    } catch (error) {
        console.error('Error loading funnel chart:', error);
        // Show error message in chart area
        ctx.getContext('2d').font = '14px Work Sans';
        ctx.getContext('2d').fillStyle = '#ef4444';
        ctx.getContext('2d').fillText('Error loading funnel data', 10, 50);
    }
}

// Call this function when page loads and when date range changes
// Add to existing initialization code (look for where other charts are loaded)
```

### Part 4: Wire Up to Refresh Logic

Find the existing chart refresh code (where `loadValidationsChart()` and other chart functions are called, likely in a `loadAllCharts()` or similar function).

Add `loadFunnelChart();` to that list:

```javascript
// Example location - find similar code in existing file
async function loadAllCharts() {
    await loadValidationsChart();
    await loadCitationsChart();
    await loadProviderChart();
    await loadFunnelChart(); // ADD THIS LINE
}
```

Also add to date range filter change handler:

```javascript
// Find the date range filter change handler
document.getElementById('date-range-filter')?.addEventListener('change', async (e) => {
    // ... existing code ...
    await loadFunnelChart(); // ADD THIS LINE
});
```

## Verification Checklist

- [ ] `/api/funnel-data` endpoint added to backend/app.py
- [ ] Endpoint returns correct JSON structure
- [ ] Endpoint handles missing log file gracefully (returns zeros)
- [ ] Endpoint accepts `from_date`, `to_date`, `variant` parameters
- [ ] Chart HTML added to dashboard/static/index.html
- [ ] Chart canvas has id="funnelChart"
- [ ] Summary stat divs have correct IDs (variant1-conversion, etc.)
- [ ] Chart JavaScript function `loadFunnelChart()` added
- [ ] Function fetches from `/api/funnel-data`
- [ ] Chart displays horizontal bars (indexAxis: 'y')
- [ ] Two datasets: Variant 1 (purple) and Variant 2 (blue)
- [ ] Tooltip shows retention percentages
- [ ] Summary stats update with conversion rates
- [ ] Chart called in initialization
- [ ] Chart refreshes when date range changes
- [ ] Chart displays correctly in browser
- [ ] No console errors
- [ ] Chart responsive (looks good at different widths)

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 92fdeb104119e21a94c79f7b38e78da0de80c8b6
- HEAD_SHA: 80a217572461d18a977030eb3b1d1272d3693264

Use git commands (git diff, git show, git log, etc.) to examine the changes.

## Review Criteria

Evaluate the implementation against these criteria:

**Adherence to Task:**
- Does implementation match task requirements?
- Were all requirements addressed?
- Any scope creep or missing functionality?

**Security:**
- SQL injection, XSS, command injection vulnerabilities
- Hardcoded secrets or credentials
- Input validation and sanitization

**Code Quality:**
- Follows project standards and patterns
- Clear naming and structure
- Appropriate error handling
- Edge cases covered

**Testing:**
- Tests written and passing
- Coverage adequate
- Tests verify actual behavior
- **Frontend visual/UX changes: Playwright tests REQUIRED for any visual or user interaction changes**

**Performance & Documentation:**
- No obvious performance issues
- Code is self-documenting or commented

## Required Output Format

Provide structured feedback in these categories:

1. **Critical**: Must fix immediately (security, broken functionality, data loss)
2. **Important**: Should fix before merge (bugs, missing requirements, poor patterns)
3. **Minor**: Nice to have (style, naming, optimization opportunities)
4. **Strengths**: What was done well

**IMPORTANT**: Verify implementation matches task requirements above.

Be specific with file:line references for all issues.