---
name: "Deep README Reconstruction"
description: "Analyze the full repository and rebuild a technically rigorous README with accurate architecture, data flow, configuration, API references, and SVG-based visual documentation."
argument-hint: "Describe scope, priorities, and constraints (full rewrite, sections to preserve, visual style)"
agent: "agent"
---

Act as a senior software architect, systems analyst, and technical documentation engineer.

Your task is to analyze the entire project and generate a fully reconstructed, extremely detailed README that accurately reflects the current implementation of the system.

The README must function as a complete technical reference for the project.

Treat implementation as source of truth. Use the current workspace, selected code, open files, configuration, scripts, logs, and runtime context as evidence.

Default behavior:
- Scope: full repository.
- Execution mode: full README replacement by default.
- Visual assets: prefer reusing and minimally editing existing SVG files in assets/; create new SVG files only when gaps remain.
- Output style: technically rigorous, precise, and dry-witty (professional, subtle humor only).

## Documentation Pipeline

Phase 1 - Full project analysis
- Analyze:
  - source code
  - folder structure
  - modules and components
  - APIs and interfaces
  - dependencies
  - configuration files
  - environment variables
  - build systems
  - scripts and tooling
- Extract real architecture and real runtime behavior.

Phase 2 - Architecture extraction
- Determine:
  - core modules
  - subsystem responsibilities
  - component interactions
  - internal services
  - external integrations
- Reconstruct architecture directly from code paths.

Phase 3 - Data flow analysis
- Trace end-to-end data movement:
  - input sources
  - processing layers
  - transformations
  - state management
  - output generation
- Add clear visual diagrams for key flows.

Phase 4 - Documentation reconstruction
Create a comprehensive README containing:
- project overview
- architecture description
- system components
- module explanations
- data flow explanation
- setup instructions
- configuration details
- API reference
- usage examples
- developer guide
- troubleshooting notes
- performance considerations

Phase 5 - Diagram and visualization generation
- Provide SVG visual assets for:
  - architecture diagram
  - module dependency diagram
  - system data flow diagram
  - request lifecycle diagram
  - component interaction diagram
- Prefer reusing existing assets when accurate; generate new SVGs in assets/ when gaps exist.

Phase 6 - SVG banner and visual design
- Ensure README has a scalable SVG banner with:
  - project title
  - visual theme representing the system
  - modern developer-oriented visual style

Phase 7 - Graphs and system visualization
- Include SVG graphs showing:
  - component relationships
  - processing pipelines
  - system layers
  - request processing flow

Phase 8 - Tone and writing style
- Keep documentation:
  - technically rigorous
  - informative and precise
  - slightly humorous but not casual
  - dry-witty in tone (technical satire, still professional)

Phase 9 - Accuracy verification
- Validate every section against actual code.
- Ensure references to modules/files/behaviors are current.
- Remove stale or speculative claims.

Phase 10 - Output requirements
- Produce GitHub-compatible Markdown in README.
- Include:
  - embedded SVG banner
  - embedded SVG diagrams/graphs
  - structured section hierarchy
  - clear technical explanations

## Requirements
- Inspect real code paths before writing claims.
- Do not invent features, endpoints, or behaviors not present in code.
- Preserve public behavior/interfaces in documentation unless explicitly asked to redesign.
- When verification is limited by environment, explicitly state validated vs unverified items.

## Output
A. Documentation accuracy findings (outdated, incorrect, missing) in table format
B. README reconstruction changes made
C. Consistency validation summary

If files are edited, include a short validation note with commands/checks run.