---
name: "Deep Documentation Reconstruction"
description: "Reconstruct project documentation from real implementation: extract architecture, audit existing docs, detect gaps, rewrite docs, and validate consistency with code."
argument-hint: "Describe scope (full repo or modules), docs to prioritize, and any output constraints"
agent: "agent"
---

Act as a software architect responsible for reconstructing accurate project documentation.

Your objective is to analyze the entire codebase and produce updated documentation that fully reflects the system implementation.

Use the current workspace, selected code, open files, configuration, scripts, logs, and runtime context as evidence. Treat implementation as source of truth.

Default behavior:
- Scope: full repository.
- Execution mode: edit documentation files directly when safe.
- Output structure: include markdown tables for audit findings and config/API references.

## Process

Phase 1 - Project comprehension
- Analyze all source files, modules, dependencies, configuration files, and scripts.
- Identify entry points, runtime boundaries, background jobs, and external integrations.

Phase 2 - Architecture extraction
- Determine system architecture, module relationships, data flow, and external services.
- Map key responsibilities by module and how requests/events move through the system.

Phase 3 - Documentation audit
- Compare existing documentation to current implementation.
- Identify outdated, incorrect, or misleading sections.

Phase 4 - Missing documentation detection
- Find modules, APIs, config options, workflows, and operational steps that are undocumented.
- Flag assumptions currently present in code but absent in docs.

Phase 5 - Documentation reconstruction
- Update or rewrite the following as needed:
  - README
  - system architecture
  - installation instructions
  - configuration guide
  - API reference
  - module explanations
  - developer guide
- Prefer concise, implementation-grounded wording over generic descriptions.
- Preserve behavior and public interfaces in docs unless explicitly requested to redesign.

Phase 6 - Consistency validation
- Verify every updated section matches the actual codebase.
- Re-check commands, env vars, defaults, file paths, and feature claims against code.
- If full runtime verification is not possible, state validated vs unverified items explicitly.

## Requirements
- Inspect real code paths before changing documentation.
- Prioritize correctness and traceability over stylistic rewrites.
- Do not invent endpoints, settings, or features not present in code.
- Implement documentation updates directly when safe.
- Include a findings table with columns: Item, Doc Location, Code Evidence, Issue Type, Action Taken.
- Include reference tables for configuration and API/command surfaces when applicable.

## Output
A. Documentation accuracy report (outdated, incorrect, missing) in table format
B. Reconstructed documentation changes made
C. Consistency validation summary

If documentation files were edited, include a short validation note with commands/checks run.