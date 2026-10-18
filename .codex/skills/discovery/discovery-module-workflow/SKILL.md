---
name: discovery-module-workflow
description: >
  Automates the visual discovery and backlog creation process for a new module. 
  Analyzes UI mockups, uses /create-prd to generate a comprehensive PRD in pt-BR, 
  and orchestrates the creation of Epics and technical Issues with PERT estimates via GitHub MCP.
---

# Discovery Module Workflow

**Goal:** map visual mockups to engineering requirements and generate a structured, estimated backlog in GitHub automatically.

**Hard rule:** you must execute strictly in phases. You wait for and validate the completion of each step before starting the next. If a validation fails, abort immediately. All generated artifacts, titles, descriptions, and PRDs MUST be written in Brazilian Portuguese (pt-BR).

## Phase 1 — Prerequisite Validations

Before generating any text, ensure the required inputs exist. There are no assumptions. 

1. **Module Validation:** Check the file system to verify if the directory `/discovery/modules/[MODULE_NAME]` exists. If it does not exist, abort the execution and report the missing path.
2. **Image Validation:** Read the confirmed directory and identify if there are valid image files (e.g., .png, .jpg, .webp). If the directory is empty or contains no images, abort the execution and state that there are no visual inputs to start the discovery process.

## Phase 2 — Discovery and Requirements Gathering

1. **Context Analysis:** Use your native vision capabilities to directly view and analyze the validated image files. Map the visual scope, user flows, data fields, and apparent business rules. DO NOT write scripts, execute bash commands, or look for local CLI tools to process these images. You must read the images directly.
2. **PRD Generation:** Actively invoke the `/create-prd` skill. Cross-reference the visual analysis with engineering best practices to exhaustively map (all output strictly in pt-BR):
   - Functional Requirements (FR).
   - Non-Functional Requirements (NFR) (focusing on performance, security, and accessibility).
   - Main use cases.
3. **Data Persistence:** Create a Markdown file with the complete gathered scope and save it EXACTLY at the path `/discovery/modules/[MODULE_NAME]/prd-[MODULE_NAME].md`. Do not proceed until this file is successfully written.

## Phase 3 — Task Orchestration (Standard GitHub MCP)

**Context:** The standard GitHub MCP tool `create_issue` requires a repository. All issues MUST be created in `HeluApp/auto-board`. Board tracking is handled automatically by the `auto-board` label.

1. **Scope Reading:** Read the final content of the generated `prd-[MODULE_NAME].md` file.
2. **Epic Creation:** Use the GitHub MCP tool to create a root Issue in `HeluApp/auto-board`.
   - **Title:** `[Epic] Módulo: [MODULE_NAME]`
   - **Body:** Include an executive summary generated from the PRD (in pt-BR).
   - **Labels:** Add the labels `epic` and `auto-board`.
   - **Mandatory Action:** Extract and store the created Issue number (ID) in your memory for the next step.
3. **Technical Task Breakdown:** Translate the PRD requirements into atomic, independent tasks. Use the MCP to create child Issues in `HeluApp/auto-board`. 
   - **PERT Calculation:** For EACH task created, you MUST apply the 3-Point Estimation Technique (PERT) to calculate the effort in hours. Define Optimistic (O), Most Likely/Realistic (M), and Pessimistic (P). Factor (F) = 2. Apply: `E = ((O-F) + 4(M-1.5F) + (P-2F)) / 6`.
   - **Frontend Issues:** Add the labels `frontend` and `auto-board`.
   - **Backend Issues:** Add the labels `backend` and `auto-board`.
   - **Mandatory Child Issue Body Structure (in pt-BR):**

```markdown
Relacionado ao Epic #[EPIC_ID]

## Descrição Técnica
[Descrição detalhada do que deve ser implementado, regras de negócio e critérios de aceite baseados no PRD]

## Estimativa PERT
- Otimista (O): [X]h
- Realista (M): [Y]h
- Pessimista (P): [Z]h
- **Esforço Esperado (E): [W] em horas [h] e minutos [m]**
```

## Gotchas
- Pt-BR only. Even though your instructions are in English, the Epic, the Issues, and the PRD must be entirely in pt-BR.
- Labels must exist. The labels epic, frontend, backend, and auto-board must exist in the target repository, or the API call will silently drop them. Do not attempt to create the labels yourself, just apply them.
- Strict linking. You cannot forget to prepend "Relacionado ao Epic #[EPIC_ID]" to child issues. This is the only way to maintain traceability without an advanced GraphQL client.
- PERT is mandatory. Do not create an issue without calculating and displaying the PERT block.
- Failsafe. If Phase 1 fails, stop. Do not hallucinate a PRD based on the module name alone.