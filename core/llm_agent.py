import os
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

# ONLY USE MODELS THAT ARE ACTUALLY LIVE NOW
PREFERRED_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]

def normalize_role(role):
    if role == "agent":
        return "assistant"
    if role in ["assistant", "system", "user"]:
        return role
    return "user"


def chat_with_llm(messages):

    safe_messages = []
    for m in messages:
        safe_messages.append({
            "role": normalize_role(m.get("role")),
            "content": m.get("content") or m.get("text") or ""
        })

    last_error = None

    for model in PREFERRED_MODELS:
        try:
            print(f"\n🔥 Using Groq Model → {model}")

            response = client.chat.completions.create(
                model=model,
                messages=safe_messages,
                temperature=0.4,
                max_tokens=1200
            )

            reply = response.choices[0].message.content
            if reply and reply.strip():
                return reply

        except Exception as e:
            last_error = e
            print("\n================ GROQ ERROR =================")
            print(e)
            print("=============================================\n")
            continue

    return (
        "I'm having trouble generating a detailed reply right now because "
        "the configured LLM model is unavailable. But don’t worry — "
        "you can continue chatting and I’ll keep responding normally 😊"
    )
