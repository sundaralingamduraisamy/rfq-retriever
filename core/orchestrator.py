from core.retriever import hybrid_search, get_full_rfq
from agents.generator import generate_rfq


def finalize_rfq(requirement: str, clarification: str):
    """
    FINAL RFQ GENERATION PIPELINE
    1. Search relevant RFQs
    2. Pull FULL original RFQ (merged chunks)
    3. Send to LLM + user details
    4. Return final professional RFQ
    """

    refs = hybrid_search(requirement)

    # ❌ No relevant RFQ in dataset
    if not refs or len(refs) == 0:
        return {
            "status": "NO_MATCH",
            "message": "No matching RFQs found in database."
        }

    # Pick best matched RFQ file
    best_file = refs[0]["file"]

    # Get COMPLETE RFQ text (no chunk cut problem)
    full_rfq_text = get_full_rfq(best_file)

    # Generate RFQ draft using LLM
    draft = generate_rfq(
        f"""
USER REQUIREMENT:
{requirement}

USER PROVIDED DETAILS:
{clarification}

REFERENCE RFQ CONTENT (Complete Original RFQ):
{full_rfq_text}
""",
        refs
    )

    return {
        "status": "SUCCESS",
        "references": refs,        # with relevance %
        "base_rfq": full_rfq_text, # full original RFQ
        "draft": draft             # AI modified RFQ
    }
