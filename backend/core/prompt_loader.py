import os
from settings import settings

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

def load_prompt(filename: str, **kwargs) -> str:
    """
    Load a markdown prompt from the prompts directory and format it with kwargs.
    
    Args:
        filename (str): The filename of the prompt (e.g., 'router_intent.md').
        **kwargs: Variables to inject into the prompt template.
        
    Returns:
        str: The formatted prompt string.
    """
    if not filename.endswith(".md"):
        filename += ".md"
        
    path = os.path.join(PROMPTS_DIR, filename)
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt file not found: {path}")
        
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    try:
        if kwargs:
            return content.format(**kwargs)
        return content
    except KeyError as e:
        raise ValueError(f"Missing variable for prompt {filename}: {e}")
    except Exception as e:
        raise ValueError(f"Error formatting prompt {filename}: {e}")
