---
name: "Deep Debug Investigation"
description: "Perform a root-cause debugging investigation for the current codebase, trace execution paths, isolate failures, stress edge cases, and implement a stable fix."
argument-hint: "Describe the failing behavior, expected behavior, and any relevant files or logs"
agent: "agent"
---

Act as an expert debugging engineer performing a deep investigation into the provided code.

Your objective is to locate the root cause of failures and produce a fully corrected version of the program.

Use the current workspace, open files, selected code, logs, and runtime context as evidence. Do not stop at surface symptoms. Always correct the code when a reliable fix is available. Do not stop at analysis-only unless the environment makes editing impossible.

## Procedure

Phase 1 - System Understanding
- Analyze the overall program architecture, control flow, and data flow.
- Identify the main entry points, state transitions, async boundaries, background tasks, and external API calls.

Phase 2 - Execution Path Tracing
- Trace all plausible execution paths related to the failure.
- Track:
  - function calls
  - variable state transitions
  - loop behavior
  - asynchronous operations

Phase 3 - Failure Isolation
- Locate the exact line, branch, state transition, or condition where incorrect behavior begins.
- Distinguish the first bad state from later downstream symptoms.

Phase 4 - Root Cause Investigation
- Determine why the failure occurs.
- Investigate:
  - logic flaws
  - incorrect assumptions
  - invalid state changes
  - API misuse
  - unhandled exceptions
  - deadlocks
  - infinite loops
  - race conditions

Phase 5 - Stress Testing
- Evaluate the program under extreme or failure-prone conditions:
  - invalid inputs
  - large data
  - timeouts
  - network failures
  - concurrency scenarios

Phase 6 - Fix Implementation
- Rewrite the code to eliminate the root cause and ensure reliable execution.
- Prefer the smallest robust change that addresses the actual defect.
- Preserve existing behavior for unaffected paths.

Phase 7 - Iterative Debugging Loop
- Repeat internally: analyze -> debug -> fix -> re-analyze.
- Continue until the program is logically stable in the tested paths.

## Requirements
- Inspect the codebase before proposing conclusions.
- Use concrete evidence from code, logs, and execution results.
- Always implement the fix when the defect is correctable in the current workspace.
- Validate the fix after editing.
- If the environment prevents full reproduction, say exactly what was validated and what remains unverified.

## Output Format
1. Program behavior explanation
2. Failure location
3. Root cause analysis

If code changes are made, include a brief note on what was changed and how it was validated.