# Part 10: Content Production Workflow

## Template Development Process

### Phase 1: Template Creation (Week 1-2)
1. **Research & Outline**
   - Analyze top 10 ranking pages for target keywords
   - Identify content gaps and unique angles
   - Map variable insertion points (minimum 8 per template)
   - Document style-specific variations needed

2. **Template Writing**
   - Write base template (1,200-1,500 words)
   - Insert {VARIABLES} with clear naming
   - Create 3+ example sets per error type
   - Write style-specific conditional content blocks
   - Include troubleshooting sections

3. **Template Review**
   - Editor review for accuracy and clarity
   - Technical review for citation rule correctness
   - SEO review for keyword placement and structure
   - Approve for production use

### Phase 2: Data Preparation (Week 2-3)
1. **Variable Database Creation**
   - Build CSV/JSON with all variable values
   - Columns: citation_style, error_type, example_correct, example_incorrect, rule_explanation, etc.
   - Validate all citation examples for accuracy
   - Cross-reference APA/MLA/Chicago style guides

2. **Quality Assurance**
   - Sample 20 random combinations
   - Generate test pages manually
   - Verify examples match error types
   - Check for nonsensical combinations
   - Validate formatting displays correctly

### Phase 3: Page Generation (Week 3-4)
1. **Scripted Generation**
   - Python/Node script merges templates + data
   - Generate all page combinations
   - Create unique meta titles/descriptions per page
   - Generate internal linking structure
   - Output as markdown or HTML

2. **Pre-Launch Checks**
   - Run Copyscape on 50 page sample
   - Verify word count minimums met
   - Check for template variable errors (missing replacements)
   - Validate URL structure consistency
   - Test pages in staging environment

## Human Review Requirements

### Sampling Strategy
- Review minimum 20% of generated pages
- Stratified sampling across:
  - All citation styles
  - All error types
  - High-priority vs low-priority keywords
  - Edge cases (unusual source types)

### Review Checklist Per Page
- [ ] Citation examples are accurate for this specific error
- [ ] Rule explanation matches the error type
- [ ] No obvious template variable failures
- [ ] Internal links are contextually relevant
- [ ] Keyword naturally integrated (not stuffed)
- [ ] Page provides unique value vs similar pages
- [ ] Mobile formatting displays correctly
- [ ] Schema markup validates
- [ ] Meta title/description unique and compelling

### Editor Responsibilities
- Approve all templates before generation
- Review 100% of high-priority pages (top 50 keywords)
- Spot-check 20% of remaining pages
- Flag pages needing manual editing
- Sign off on batch launch

## Update & Maintenance Workflow

### Quarterly Content Refresh
1. **Performance Analysis**
   - Identify pages with high impressions, low CTR
   - Find pages with high bounce rate
   - Detect pages losing rankings

2. **Content Updates**
   - Add new examples based on user questions
   - Expand thin sections
   - Update for style guide changes
   - Improve formatting/readability
   - Add FAQ sections for ranking pages

3. **Technical Updates**
   - Refresh last-modified dates
   - Update internal linking
   - Fix any broken links
   - Re-validate schema markup
   - Check mobile rendering

### Style Guide Change Response
When APA/MLA/Chicago releases updates:
1. Identify affected pages (tag system required)
2. Prioritize updates by traffic
3. Update templates + regenerate affected pages
4. Add "Updated for [Style] 8th Edition" badges
5. Submit updated sitemap to GSC

## Tools & Infrastructure

### Required Tools
- **Content generation**: Python/Node + Jinja2 or Handlebars
- **Quality checks**: Copyscape API, Grammarly API
- **SEO validation**: Screaming Frog, Ahrefs/Semrush
- **Monitoring**: Google Search Console API, custom dashboard
- **Version control**: Git for templates and scripts

### Data Management
- Master spreadsheet for variable data
- Version control for all content changes
- Backup before each generation run
- Track which template version generated which pages
- Document all manual edits to generated pages

## Production Timeline (Per Batch)

### Minimum 3-Week Cycle
- **Week 1**: Template creation + review + approval
- **Week 2**: Data prep + QA + test generation
- **Week 3**: Full generation + human review + staged launch

### Capacity Estimates
- 1 writer can create 2-3 templates/week
- 1 editor can review 50 pages/day
- Can generate 500+ pages/week (automated)
- Realistically launch 200-300 high-quality pages/month with proper review

## Success Metrics

### Production Quality KPIs
- Template approval rate on first review: >80%
- Pages requiring manual fixes: <10%
- Copyscape uniqueness score: >70% avg
- Editor review time per page: <10 minutes

### SEO Performance KPIs
- Index rate within 2 weeks: >80%
- Pages ranking top 50 within 30 days: >25%
- Avg time on page: >90 seconds
- Bounce rate: <60%
- Pages with featured snippets: >5%