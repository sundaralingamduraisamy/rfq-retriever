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
    
    # Set torch logging to ERROR only
    logging.getLogger("torch").setLevel(logging.ERROR)
    
    # Set sentence_transformers logging to ERROR only
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Reduce uvicorn access log verbosity
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
