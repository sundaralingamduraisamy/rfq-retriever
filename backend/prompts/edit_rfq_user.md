Instruction:
{instruction}

Rules for this task:
1. Apply the instruction to the text below.
2. Output the **FULL** document with the changes applied.
3. **HIGH VERBOSITY REQUIRED**: Every section must contain detailed technical requirements, safety standards (ISO/IATF), and specific parameters retrieved from the SEARCHED TECHNICAL CONTEXT.
4. **PROFESSIONAL FORMAT**: Ensure all sections use `## [Number]. [Title]` format for alignment with the document structure.
5. **NO MANUAL TOC**: Do NOT generate a manual "Table of Contents" list.
5. **DO NOT** return just the changed part or use placeholders like "...".
6. Output ONLY the updated text. No comments.

--- SEARCHED TECHNICAL CONTEXT ---
{context_documents}

--- CURRENT RFQ CONTENT ---
{current_text}
