---
name: "Deep Optimization Audit"
description: "Run a deep performance and maintainability optimization audit: detect redundancy, simplify control flow, improve algorithms, reduce memory/IO overhead, consolidate code, and verify unchanged behavior."
argument-hint: "Describe target module/files, workload profile, and constraints (latency/memory/readability)"
agent: "agent"
---

Act as a software performance engineer performing a deep optimization audit.

Your goal is to remove all redundancy and optimize the program for efficiency, clarity, and maintainability.

Use the current workspace, selected code, open files, logs, and runtime context as evidence. Optimize only when behavior can be preserved or safely validated.

## Optimization Pipeline

Phase 1 - Full code comprehension
- Understand architecture, control flow, and data flow.
- Identify entry points, hot paths, async boundaries, and external dependencies.

Phase 2 - Redundancy detection
- Identify duplicated logic, repeated computation, unnecessary variables, redundant loops, and repeated API calls.

Phase 3 - Control flow simplification
- Refactor nested conditionals and complex branching into simpler, clearer logic structures.

Phase 4 - Algorithm improvement
- Replace inefficient algorithms or data access patterns with more efficient alternatives where safe.

Phase 5 - Memory efficiency
- Reduce unnecessary allocations, redundant data structures, repeated copying, and avoidable cache churn.

Phase 6 - IO and API efficiency
- Minimize expensive operations such as network requests, file reads, and repeated serialization/deserialization.

Phase 7 - Code consolidation
- Extract reusable helpers for duplicated logic while preserving readability.

Phase 8 - Behavior verification
- Ensure functionality remains unchanged after optimization.
- Re-run compile/tests/targeted runtime checks where available.

## Requirements
- Inspect real code paths before proposing optimizations.
- Prioritize measurable impact and avoid speculative micro-optimizations.
- Preserve public behavior and interfaces unless explicitly requested otherwise.
- Implement safe optimizations directly when feasible.
- If full verification is blocked by environment constraints, state what was validated and what remains unverified.

## Output
A. Redundancy report
B. Performance issues detected
C. Optimization explanations

If code changes are made, include a short validation note with commands/checks run.