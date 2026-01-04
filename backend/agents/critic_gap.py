from core.llm_provider import llm
from core.prompt_loader import load_prompt
from langchain_core.messages import SystemMessage, HumanMessage

def gap_review(draft_text):
    if not draft_text or draft_text.strip() == "":
        return "No draft available to review for gaps."

    prompt = load_prompt("gap_review.md", draft_text=draft_text)

    try:
        response = llm.invoke([
            SystemMessage(content="You are a strict RFQ quality auditor."),
            HumanMessage(content=prompt)
        ])

        return response.content

    except Exception as e:
        return f"Gap Review Failed: {str(e)}"
