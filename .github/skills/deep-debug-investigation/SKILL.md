---
name: deep-debug-investigation
description: 'Perform end-to-end root-cause debugging for code failures: system mapping, execution tracing, failure isolation, root-cause proof, stress testing, targeted fixes, and iterative revalidation.'
argument-hint: 'Describe failing behavior, expected behavior, and relevant files or runtime context'
user-invocable: true
---

# Deep Debug Investigation

Use this skill when a bug needs a full engineering investigation, not a quick patch.

## Outcomes
- Explain what the program currently does and why.
- Isolate where incorrect behavior starts.
- Identify root cause with evidence.
- Implement a stable fix and re-validate under stress.

## Inputs To Gather First
- Observed failure symptoms.
- Expected behavior.
- Entry points (commands, APIs, events).
- Runtime constraints (timeouts, API keys, concurrency limits, environment).

## Procedure
1. Phase 1: System Understanding
- Map architecture, modules, and ownership boundaries.
- Identify control flow between entry points and side effects.
- Track data flow for critical state variables and persistence.

2. Phase 2: Execution Path Tracing
- Trace happy path and edge paths from entry to output.
- Track function calls, variable transitions, loop exit conditions, and async task boundaries.
- Record where state is mutated and where external I/O happens.

3. Phase 3: Failure Isolation
- Reproduce or simulate the failure path.
- Identify the first incorrect state or branch decision.
- Pinpoint exact function and condition where behavior diverges.

4. Phase 4: Root Cause Investigation
- Validate why divergence occurs:
- logic flaw
- invalid assumption
- state corruption
- API misuse
- unhandled exception
- deadlock/infinite loop/race condition
- Confirm root cause by proving the issue disappears when condition is corrected.

5. Phase 5: Stress Testing
- Validate behavior under:
- invalid inputs
- oversized data
- timeout/network failure
- concurrency contention
- Ensure fallback/error paths are deterministic and safe.

6. Phase 6: Fix Implementation
- Apply the minimal robust change at the root cause location.
- Preserve existing behavior for unaffected paths.
- Add guards for invalid state transitions and failure-prone API calls.

7. Phase 7: Iterative Loop
- Re-run: analyze -> debug -> fix -> re-analyze.
- Continue until no reproducible incorrect behavior remains in tested paths.

## Decision Rules
- If failure is not reproducible: instrument logging and trace state transitions before changing logic.
- If multiple candidate causes exist: fix one variable at a time and re-test to avoid false attribution.
- If async/concurrency is involved: prioritize ordering, shared state mutation, and timeout handling.
- If external APIs are involved: test degraded modes first (timeouts, non-200, malformed payloads).

## Completion Criteria
- Root cause is tied to a concrete condition and code location.
- Fix passes normal path plus defined stress scenarios.
- No new lint/syntax/runtime errors introduced.
- Final report includes:
1. Program behavior explanation
2. Failure location
3. Root cause analysis

## Reporting Template
1. Program behavior explanation
- Current architecture and end-to-end flow summary.
- Actual vs expected behavior.

2. Failure location
- First incorrect branch/state and exact function/condition.

3. Root cause analysis
- Why the failure occurs.
- What assumption was invalid.
- Why the implemented fix is correct and stable.
