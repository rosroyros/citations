#!/bin/bash

# Create all Beads tasks for Gated Validation Results implementation
# This script creates 19 granular tasks with proper dependency structure

echo "Creating Beads tasks for Gated Validation Results implementation..."

# Task 1: Database Migration
TASK1=$(bd create "Database schema extension for gated results tracking" -t task -p 0 -d "$(cat <<'EOF'
Add database schema extensions to support gated results engagement tracking.

## Context & Rationale
Without database schema changes, we cannot store engagement metrics. This is the foundational blocker for all tracking functionality. SQLite ALTER TABLE approach ensures backward compatibility.

## Key Implementation Details
- Add 5 new columns to validations table with NULL defaults
- Create indexes for query performance optimization
- Ensure backward compatibility with existing data
- Provide rollback capability

## Schema Changes
```sql
ALTER TABLE validations
ADD COLUMN results_ready_at TEXT DEFAULT NULL,
ADD COLUMN results_revealed_at TEXT DEFAULT NULL,
ADD COLUMN time_to_reveal_seconds INTEGER DEFAULT NULL,
ADD COLUMN results_gated BOOLEAN DEFAULT FALSE,
ADD COLUMN gated_outcome TEXT DEFAULT NULL;
```

## Acceptance Criteria
- All new columns added with NULL defaults
- Database functions normally after migration
- No existing data corrupted or lost
- Rollback script tested and working

## Technical Considerations
- Maintain existing validation performance
- Follow existing database patterns
- Ensure deployment safety with rollback procedure
EOF
)" --json | jq -r '.id')
echo "Created task 1: $TASK1"

# Task 2: Backend Foundation
TASK2=$(bd create "Backend foundation for gated results tracking" -t task -p 0 -d "$(cat <<'EOF'
Implement backend infrastructure for gated results detection and tracking.

## Context & Rationale
Backend needs infrastructure to determine when to gate results and how to store engagement data. This creates the foundation for all tracking functionality while maintaining existing validation performance.

## Key Components
- Gating logic function (should_gate_results)
- Tracking data models and validation
- Database helper functions for engagement tracking
- Logging infrastructure for dashboard parsing

## Gating Logic
```python
def should_gate_results(user_type: str, results: dict) -> bool:
    return (
        user_type == 'free' and
        results.get('isPartial') is False and
        results.get('errors') == []
    )
```

## Acceptance Criteria
- Gating logic correctly identifies free vs paid users
- Tracking models validate and store engagement data
- Logging events properly formatted for dashboard parsing
- Errors don't break core validation functionality
- Performance impact minimal

## Dependencies
- Database schema must be migrated first
EOF
)" --json | jq -r '.id')
echo "Created task 2: $TASK2"

# Task 3: Frontend Foundation
TASK3=$(bd create "Frontend foundation for gated results state management" -t task -p 0 -d "$(cat <<'EOF'
Implement frontend state management foundation for gated results functionality.

## Context & Rationale
Frontend needs new state management to handle gated results without breaking existing validation flow. This creates the foundation for UI implementation while maintaining compatibility with existing job recovery logic.

## State Management Structure
```javascript
// New state variables
const [resultsReady, setResultsReady] = useState(false)
const [resultsRevealed, setResultsRevealed] = useState(false)
const [resultsReadyTimestamp, setResultsReadyTimestamp] = useState(null)

// State flow: loading → resultsReady → resultsRevealed
```

## Key Components
- React state integration in App.jsx
- Timing tracking for reveal measurements
- State transition logic
- Client-side tracking data structure
- Basic error boundaries

## Acceptance Criteria
- New state variables integrated without breaking existing flow
- Timing tracking accurately measures reveal time
- State transitions work correctly for all user types
- Compatible with existing job recovery logic
- Error boundaries prevent component crashes

## Technical Considerations
- Follow existing React patterns in App.jsx
- Maintain performance with minimal re-renders
- Ensure backward compatibility
EOF
)" --json | jq -r '.id')
echo "Created task 3: $TASK3"

# Task 4: Feature Flag
TASK4=$(bd create "Environment variable feature flag for gated results" -t task -p 0 -d "$(cat <<'EOF'
Implement simple environment variable feature flag for gated results functionality.

## Context & Rationale
Simple on/off control enables immediate disable if issues arise. This provides operational safety without adding deployment complexity, following project's pragmatic approach.

## Implementation
- Environment variable: GATED_RESULTS_ENABLED=true/false
- Frontend flag checking in App.jsx
- Backend flag checking in validation completion
- Flag validation on application startup

## Usage Pattern
```bash
# Enable gated results
GATED_RESULTS_ENABLED=true

# Disable gated results (fallback to current behavior)
GATED_RESULTS_ENABLED=false
```

## Acceptance Criteria
- Feature flag disables gated functionality when false
- Both frontend and backend respect flag setting
- No impact on existing functionality when disabled
- Flag changes require application restart
- Deployment configuration includes flag

## Technical Considerations
- Simple boolean flag (no percentage-based complexity)
- Immediate disable capability for operational safety
- Consistent behavior across frontend and backend
EOF
)" --json | jq -r '.id')
echo "Created task 4: $TASK4"

# Task 5: Analytics Foundation
TASK5=$(bd create "Analytics infrastructure for engagement tracking" -t task -p 0 -d "$(cat <<'EOF'
Create analytics infrastructure for gated results engagement tracking.

## Context & Rationale
Analytics foundation needed for GA4 events and dashboard integration. Simple implementation follows existing project patterns while providing comprehensive tracking capabilities.

## Analytics Components
- GA4 event tracking function (results_revealed)
- Event parameter validation
- Log event formatting utilities
- Timing data collection helpers
- Integration with existing analytics system

## GA4 Event Structure
```javascript
window.gtag('event', 'results_revealed', {
  job_id: jobId,
  time_to_reveal_seconds: timeToReveal,
  user_type: 'free',
  validation_type: 'gated'
});
```

## Acceptance Criteria
- GA4 events fire correctly when results are revealed
- Log events properly formatted for dashboard parsing
- Timing data accurately collected and transmitted
- No interference with existing analytics
- Event validation prevents malformed data

## Technical Considerations
- Follow existing analytics.js utility patterns
- Fire-and-forget approach (no retry logic)
- Minimal performance impact
- Compatible with existing tracking infrastructure
EOF
)" --json | jq -r '.id')
echo "Created task 5: $TASK5"

# Task 6: Testing Framework
TASK6=$(bd create "Testing framework setup for gated results functionality" -t task -p 0 -d "$(cat <<'EOF'
Set up comprehensive testing framework for gated results using TDD approach.

## Context & Rationale
TDD approach required by project standards. Testing framework setup enables test-first development for all components, ensuring quality and maintainability.

## Testing Components
- React component testing framework
- Backend API integration testing
- Playwright end-to-end testing setup
- Test data fixtures for gated scenarios
- Testing patterns and utilities

## Test Categories
- Unit Tests: React component logic, backend endpoints
- Integration Tests: End-to-end gated flow validation
- Playwright Tests: User interactions, visual regression

## Acceptance Criteria
- Unit testing framework configured for React components
- Integration testing ready for API endpoints
- Playwright tests can simulate user interactions
- Test fixtures cover all gating scenarios
- TDD patterns established for development

## Technical Considerations
- Follow existing project testing patterns
- Ensure CI/CD integration compatibility
- Create realistic test data scenarios
- Maintain test performance and reliability
EOF
)" --json | jq -r '.id')
echo "Created task 6: $TASK6"

# Task 7: Documentation Review
TASK7=$(bd create "Final documentation review and implementation planning" -t task -p 0 -d "$(cat <<'EOF'
Conduct final review of design documentation and prepare implementation guidance.

## Context & Rationale
Final review ensures implementation team has complete understanding and all design decisions are properly documented with Oracle feedback addressed.

## Review Components
- Complete design document validation
- Oracle concern resolution verification
- Implementation approach confirmation
- Final decision documentation
- Implementation handoff preparation

## Key Documents
- Design document: docs/plans/2025-11-28-gated-validation-results-design.md
- Oracle review analysis with decisions
- Implementation plan with dependencies
- Risk assessment and mitigations

## Acceptance Criteria
- Design document complete with Oracle feedback addressed
- Implementation plan clear and actionable
- All design decisions properly documented with rationale
- Team ready for development with clear guidance
- Risk assessment and mitigation strategies defined

## Deliverables
- Updated design document with Oracle review section
- Comprehensive implementation plan
- Risk assessment with mitigation strategies
- Decision rationale documentation
EOF
)" --json | jq -r '.id')
echo "Created task 7: $TASK7"

echo "Phase 1 foundation tasks created: $TASK1, $TASK2, $TASK3, $TASK4, $TASK5, $TASK6, $TASK7"