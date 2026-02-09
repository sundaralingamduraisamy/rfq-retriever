Instruction:
{instruction}

Rules for this task:
1. Apply the instruction to the text below.
2. Output the **FULL** document with the changes applied.
3. **HIGH VERBOSITY REQUIRED**: Every section must contain detailed technical requirements, safety standards (ISO/IATF), and specific parameters retrieved from the SEARCHED TECHNICAL CONTEXT.
4. **PROFESSIONAL FORMAT**: Ensure all sections use `## [Number]. [Title]` format for alignment with the document structure.
5. **NO MANUAL TOC**: Do NOT generate a manual "Table of Contents" list.
6. **IMAGE PLACEMENT - CRITICAL**: If you see "CRITICAL - ATTACHED IMAGE: [[IMAGE_ID:n]]" in the context below:
   - Place the `[[IMAGE_ID:n]]` tag on its own line IMMEDIATELY AFTER the relevant section heading
   - Example: After `## 8. TECHNICAL SPECIFICATIONS`, insert a blank line, then `[[IMAGE_ID:10]]`, then another blank line
   - DO NOT create subsections like "8.1 Image of..." - just insert the tag directly
   - The tag will automatically render as an image in the preview
7. **DO NOT** return just the changed part or use placeholders like "...".
8. Output ONLY the updated text. No comments.

--- SEARCHED TECHNICAL CONTEXT ---
{context_documents}

--- CURRENT RFQ CONTENT ---
{current_text}
