# from pydantic import BaseModel
# from typing import List, Dict, Any

# class ChatState(BaseModel):
#     messages: List[Dict[str, str]] = []  # Chat history
#     intent: Dict[str, Any] = {}          # Intent: {category, price_range, quantity, missing}
#     products: List[Dict[str, Any]] = []  # Firestore products
#     needs_clarification: bool = False    # Flag for clarification
#     clarification_question: str = ""     # Current clarification question
#     clarification_turn: int = 0          # Tracks clarification attempts


from pydantic import BaseModel
from typing import List, Dict, Any

class ChatState(BaseModel):
    messages: List[Dict[str, str]] = []  # Chat history
    products: List[Dict[str, Any]] = []  # Firestore products