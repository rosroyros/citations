# Citation Format & Style Checker - Project Overview

## Project Vision

Build a website that verifies citation format correctness and style compliance for academic bibliographies. The tool will check if existing citations follow proper formatting rules and taxonomy for specific citation styles (initially focusing on APA), rather than generating citations or verifying source validity.

---

## Problem Statement

### Core User Need
Researchers, students, and academics need to verify that their manually-written or generated citations conform to specific style guide requirements (APA, MLA, Chicago, etc.). They want to ensure:
- Proper formatting is applied
- Taxonomy and conventions are followed correctly
- All required elements are present and in the correct order
- Punctuation, capitalization, and spacing are accurate

### Market Gap Identified
Our research revealed a significant gap in the market:
- **Citation generators dominate** - Tools like EasyBib, Citation Machine, and Scribbr focus on creating citations, not validating them
- **True format validators are rare** - Very few tools actually check if existing citations are formatted correctly
- **Existing validators are limited** - Current options like David Weiss's APA Citation Checker primarily verify in-text/reference list agreement rather than comprehensive format validation
- **Quality concerns** - Users report that even popular citation generators produce error-ridden output, creating demand for validation

---

## Target Users

### Primary Users
1. **Graduate Students** - Writing theses and dissertations with extensive bibliographies
2. **PhD Candidates** - Preparing research papers and journal submissions
3. **Academic Researchers** - Submitting to journals with strict citation requirements
4. **Undergraduate Students** - Learning proper citation practices for papers

### Secondary Users
1. **Academic Writing Centers** - Supporting students with citation formatting
2. **Journal Editors** - Reviewing submissions for citation compliance
3. **Professional Writers** - Working on academic or research-based content

---

## Initial Scope

### Phase 1 - MVP Features
- **Style Support**: APA (7th edition) initially
- **Input Method**: Accept citations via text input or Word document upload
- **Validation Checks**:
  - Format compliance (punctuation, capitalization, italics)
  - Element presence and order
  - Common APA errors (author formatting, date placement, title capitalization)
  - In-text citation and reference list matching
- **Output**: Clear error reporting with specific formatting issues identified
- **Pricing**: Research both free and paid tier options

### Future Expansion (Post-MVP)
- Additional citation styles (MLA, Chicago, Harvard, IEEE)
- Integration with reference managers (Zotero, Mendeley)
- Browser extension
- Advanced validation rules
- Batch processing for entire documents
- API for institutional use

---

## Competitive Landscape

### Direct Competitors (Limited)
1. **David Weiss APA Citation Checker**
   - Checks agreement between in-text citations and references
   - Free, basic interface
   - Limited to cross-referencing, not format validation

2. **Trinka Citation Checker**
   - Automated citation analysis
   - Part of larger grammar/writing platform
   - Specific capabilities unclear from research

### Indirect Competitors (Citation Generators)
- **Scribbr** - Citation generator with editing services
- **EasyBib / Citation Machine** - Popular free citation generators
- **Zotero / Mendeley** - Reference managers with citation output
- **Grammarly Premium** - Includes some citation checking features

### Key Insight
The market is dominated by generators rather than validators. This represents an opportunity for a specialized validation tool that solves the "double-check" use case.

---

## Technical Considerations

### Required Capabilities
1. **Citation Parsing** - Extract and identify citation components
2. **Style Rule Engine** - Encode APA formatting rules programmatically
3. **Pattern Matching** - Identify citation types (book, journal, website, etc.)
4. **Error Detection** - Flag specific formatting violations
5. **Document Processing** - Handle Word documents and text input

### Potential Technical Approaches
- Rule-based validation system
- Pattern matching with regular expressions
- Citation parsing libraries (if available)
- LLM integration for complex validation scenarios
- Reference data for author name formatting, journal abbreviations, etc.

---

## Business Model Options

### Freemium Model
- **Free Tier**: Limited citations per month (10-20), basic validation
- **Paid Tier**: Unlimited citations, advanced checks, batch processing, priority support
- **Institutional**: Site licenses for universities and research organizations

### Pricing Research Needed
- Competitive pricing analysis
- User willingness to pay surveys
- Cost structure based on technical implementation

---

## Success Metrics

### User Engagement
- Number of citations validated per month
- Return user rate
- Average citations per session

### Quality Metrics
- Validation accuracy rate
- False positive/negative rates
- User satisfaction scores

### Business Metrics
- Free to paid conversion rate
- Monthly recurring revenue
- Customer acquisition cost

---

## Open Questions & Research Gaps

### From Previous Research
1. **Reddit/Community Feedback** - Need to search r/GradSchool, r/PhD, r/AskAcademia for authentic user pain points
2. **Citation Generator Error Patterns** - Need specific data on most common errors to prioritize validation rules
3. **User Workflow Integration** - How do users currently check citations? Manual review? Asking advisors?
4. **Institutional Demand** - Would universities pay for institutional licenses?

### Technical Questions
1. What citation parsing libraries exist?
2. How complex is encoding APA rules programmatically?
3. Can we access official APA style guide data?
4. What's the technical feasibility of Word document processing?

### Market Questions
1. What's the actual market size beyond search volume estimates?
2. What would users pay for this service?
3. Are there regulatory/licensing considerations with APA style?

---

## Next Steps

1. **Community Research** - Conduct Reddit and forum research on citation pain points
2. **Technical Proof of Concept** - Build basic APA citation validator for common citation types
3. **User Interviews** - Talk to 10-15 graduate students and researchers about their citation workflow
4. **Competitive Analysis Deep Dive** - Test existing tools thoroughly to identify gaps
5. **APA Licensing Research** - Investigate any restrictions on building APA validation tools
6. **Pricing Strategy** - Develop pricing model based on value proposition and costs
7. **MVP Specification** - Create detailed feature specifications for first version

---

## Project Status

**Current Phase**: Research & Planning  
**Last Updated**: October 2025  
**Key Decision Point**: Validate market demand through user interviews before building MVP