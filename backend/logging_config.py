import logging
import warnings
import os

def setup_logging():
    """Configure logging for the application"""
    
    # Suppress warnings from third-party libraries
    warnings.filterwarnings("ignore", category=UserWarning, module="transformers")
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # Set transformers logging to ERROR only
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    logging.getLogger("transformers").setLevel(logging.ERROR)
    logging.getLogger("transformers.tokenization_utils_base").setLevel(logging.ERROR)
    
    # Set torch and other ML libraries logging to ERROR only
    logging.getLogger("torch").setLevel(logging.ERROR)
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
    
    # Reduce HTTP-related noise (LangChain/Groq use these)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Reduce LangChain internal noise
    logging.getLogger("langchain").setLevel(logging.WARNING)
    
    # Configure root logger to WARNING for a cleaner terminal
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s'
    )
    
    # Explicitly set uvicorn logs
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
