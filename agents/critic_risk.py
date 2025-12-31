from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def risk_review(draft_text):
    if not draft_text or draft_text.strip() == "":
        return "No draft available to review for risks."

    prompt = f"""
You are a legal & procurement risk expert.

Task:
- Review RFQ draft
- Identify legal risks
- Contract risks
- Warranty risks
- SLA risks
- Compliance risks

RFQ Draft:
{draft_text}

Return structured report:
- Legal Risks
- Commercial Risks
- SLA Risks
- Compliance Risks
- Mitigation Suggestions
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You analyze RFQs and find risks."
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
        return f"Risk Review Failed: {str(e)}"
