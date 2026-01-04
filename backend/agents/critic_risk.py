from core.llm_provider import llm
from core.prompt_loader import load_prompt
from langchain_core.messages import SystemMessage, HumanMessage

def risk_review(draft_text):
    if not draft_text or draft_text.strip() == "":
        return "No draft available to review for risks."

    prompt = load_prompt("risk_review.md", draft_text=draft_text)

    try:
        response = llm.invoke([
            SystemMessage(content="You analyze RFQs and find risks."),
            HumanMessage(content=prompt)
        ])

        return response.content

    except Exception as e:
        return f"Risk Review Failed: {str(e)}"
