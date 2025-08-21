from langchain_core.tools import tool
from config.llm_config import get_llm
from prompt.prompts import clarification_prompt

llm = get_llm()

@tool
def clarifier_tool(query: str, missing: list) -> str:
    """Generate clarification question for missing intent fields."""
    if not llm:
        return "Clarification service unavailable. Please rephrase."

    try:
        chain = clarification_prompt | llm
        response = chain.invoke({"query": query, "missing": missing}).content
        print(f"[Clarifier] Query: {query}, Missing: {missing}, Response: {response}")
        return response
    except Exception as e:
        print(f"[Clarifier ERROR] {str(e)}")
        return "Could you clarify what you're looking for?"
