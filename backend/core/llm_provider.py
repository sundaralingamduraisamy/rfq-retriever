"""
config/llm_provider.py - Multi-provider LLM utility with parallel call support
Supports: OpenAI, Anthropic, Groq, Google
NO TOKEN LIMITS - Providers use their native max context
"""
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from settings import settings


def _create_llm_instance(provider: str, model: str, api_key: str, temperature: float = None):
    """
    Helper function to create LLM instance based on provider.
    Supports: openai, anthropic, groq, google
    NO TOKEN LIMITS - Providers use their native max context
    """
    provider = provider.lower()
    temp = temperature or settings.LLM_TEMPERATURE
    callbacks = [StreamingStdOutCallbackHandler()]

    if provider == "openai":
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temp,
            callbacks=callbacks
        )

    elif provider == "anthropic":
        return ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=temp,
            callbacks=callbacks
        )

    elif provider == "groq":
        return ChatGroq(
            model=model,
            api_key=api_key,
            temperature=temp,
            callbacks=callbacks
        )

    elif provider == "google":
        return ChatGoogleGenerativeAI(
            model=model,
            api_key=api_key,
            temperature=temp,
            callbacks=callbacks
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: openai, anthropic, groq, google"
        )


def get_llm(temperature: float = None):
    """
    Get default LLM instance from settings.
    NO TOKEN LIMITS
    """
    return _create_llm_instance(
        provider=settings.LLM_PROVIDER,
        model=settings.LLM_MODEL_NAME,
        api_key=settings.LLM_API_KEY,
        temperature=temperature
    )

def get_conflict_llm(temperature: float = None):
    """
    Get Conflict Detection specialized LLM.
    Falls back to default LLM if CONFLICT_LLM_PROVIDER is not set.
    """
    if settings.CONFLICT_LLM_PROVIDER and settings.CONFLICT_LLM_API_KEY:
        return _create_llm_instance(
            provider=settings.CONFLICT_LLM_PROVIDER,
            model=settings.CONFLICT_LLM_MODEL,
            api_key=settings.CONFLICT_LLM_API_KEY,
            temperature=temperature or settings.CONFLICT_LLM_TEMPERATURE
        )
    
    # Fallback to default
    return get_llm(temperature)

# Global LLM instances
llm = get_llm()
conflict_llm = get_conflict_llm()
