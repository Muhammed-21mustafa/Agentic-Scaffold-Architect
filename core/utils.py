import re

def extract_json(text: str) -> str:
    """
    Extracts the first valid JSON block or object from the given text using regex.
    This safely bypasses conversational text or hallucinated markdown wrappers from the LLM.
    """
    if not text:
        return ""
    
    # Check for ```json ... ``` markdown block
    json_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
    if json_block_match:
        return json_block_match.group(1).strip()
    
    # Fallback: Find the first { and the last }
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx + 1]
    
    # If no wrapper or brackets found, just return original string (might be empty/invalid)
    return text.strip()


def extract_markdown(text: str) -> str:
    """
    Cleans up the markdown output from the LLM.
    If the LLM wrapped everything in ```markdown ... ```, it extracts the inner content.
    """
    if not text:
        return ""
        
    md_block_match = re.search(r'^```(?:markdown)?\s*([\s\S]*?)\s*```$', text.strip(), re.IGNORECASE)
    if md_block_match:
        return md_block_match.group(1).strip()
        
    return text.strip()
