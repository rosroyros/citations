# Code Review: MLA PSEO Generation & Validation Scripts

## Critical Issues
1. **Unused Validation Gate (TF-IDF)**: 
   - In `backend/pseo/scripts/validate_mla_batch.py`, the method `check_tfidf_distinctness` is defined but **never called**.
   - The `validate_all` method calls `validate_page` loop, but `check_tfidf_distinctness` (which requires comparing all pages against APA pages) is not invoked.
   - **Impact**: The "TF-IDF similarity to APA < 0.3" requirement is NOT being enforced.

## Important Issues
1. **Missing Dependency**:
   - `validate_mla_batch.py` imports `TfidfVectorizer` and `cosine_similarity` from `sklearn` (scikit-learn), but `scikit-learn` is **not listed in `requirements.txt`**.
   - This will cause runtime errors in environments where it's not manually installed (e.g., CI/CD, other devs).

2. **Missing Test Coverage (TF-IDF)**:
   - `test_mla_scripts.py` does not contain any tests for `check_tfidf_distinctness`.
   - While other gates are tested (word count, template vars, etc.), the complex logic of TF-IDF comparison remains untested.

3. **Weak Test Coverage (Generation Script)**:
   - `test_generate_pilot_pages_dry_run` only executes the `--help` command.
   - There is no test that verifies the generator script actually runs (even in a dry-run or mocked mode) or produces files. The "comprehensive" test claim is overstated for `generate_mla_pages.py`.

## Minor Issues
1. **Import Style in Tests**:
   - `test_mla_scripts.py` modifies `sys.path` globally at the module level: `sys.path.insert(0, str(SCRIPTS_DIR))`.
   - **Suggestion**: Consider moving this into the `scripts_dir` fixture or using `PYTHONPATH` during test execution to avoid side effects on other tests.

## Strengths
- **Modular Validation Tests**: The validation logic is well-tested by importing the `MLAPageValidator` class and testing individual gate methods (except TF-IDF).
- **Fixture Usage**: Good use of `pytest` fixtures for temporary directories and sample content.
- **Config Validation**: Tests properly verify the structure of the JSON configuration files.

## Recommendation
**Request Changes**. The missing dependency and the unconnected TF-IDF validation gate need to be addressed before this task can be considered complete according to requirements. The generation script test should also be strengthened to at least attempt a mock generation.