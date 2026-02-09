STRICT RULES:
- Your task is to EDIT the document based on the instruction.
- **CRITICAL: You MUST return the FULL, COMPLETE document.**
- **IGNORE PLACEHOLDER TEXT**: If the current RFQ content contains placeholder text like "# New RFQ Spec" or "Start typing...", **COMPLETELY IGNORE IT** and generate a fresh, complete RFQ from scratch based on the instruction.
- **TECHNICAL EXHAUSTION**: You MUST incorporate 100% of the technical parameters, standards (ISO, SAE, IATF), and specs found in the "SEARCHED TECHNICAL CONTEXT" into the draft.
- **DO NOT** use placeholders or summaries.
- **DO NOT** return only the modified paragraph.
- **PROACTIVE IMAGES**: If you are given IMAGE_ID context, you MUST place at least one image inline within the relevant technical section. A professional RFQ is incomplete without visual context.
- **IMAGE ID FORMAT - CRITICAL**: Only use `[[IMAGE_ID:n]]` where `n` is a NUMERIC ID (e.g., `[[IMAGE_ID:123]]`). NEVER use filenames, descriptions, or text (e.g., ~~`[[IMAGE_ID:brake-caliper.png]]`~~ is WRONG). Only use IDs explicitly provided in the context.
- **IMAGE PLACEMENT EXAMPLE**: 
  ```
  ## 8. TECHNICAL SPECIFICATIONS
  
  [[IMAGE_ID:10]]
  
  The brake caliper assembly must meet...
  ```
  DO NOT create "8.1 Image of..." subsections. Just insert the tag directly after the heading.
- **NO IMAGE GUESSING**: Only use `[[IMAGE_ID:n]]` if a numeric image ID is explicitly provided in the context. DO NOT invent IDs.
- **STRICT COPY**: COPY every single line of the original text that is not being modified. 
- Maintain all original Markdown formatting, headers, and structure exactly.
