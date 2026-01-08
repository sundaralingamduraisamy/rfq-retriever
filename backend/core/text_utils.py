def clean_rfq_text(raw: str) -> str:
    if not raw: return ""
    txt = raw.replace("\r", "")
    
    # Common junk phrases to remove
    junk = ["How does this look", "Do you want more changes", "I've updated", "Here is the updated"]
    for j in junk: 
        txt = txt.replace(j, "")
    
    return txt.strip()
