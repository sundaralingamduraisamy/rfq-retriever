from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def gap_review(draft_text):
    if not draft_text or draft_text.strip() == "":
        return "No draft available to review for gaps."

    prompt = f"""
You are a procurement compliance and RFQ quality assurance expert.

Task:
- Review this RFQ draft
- Identify missing sections
- Identify weak / incomplete clauses
- Identify contradictions
- Identify unclear requirements

RFQ Draft:
{draft_text}

Return a structured GAP REPORT with:
- Missing Mandatory Sections
- Weak / Incomplete Clauses
- Ambiguities
- Recommendations
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict RFQ quality auditor."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Gap Review Failed: {str(e)}"
