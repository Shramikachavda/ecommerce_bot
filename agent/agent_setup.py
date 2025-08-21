# import json
# from typing import Dict, Any
# from langgraph.graph import StateGraph, END
# from prompt.prompts import intent_prompt, response_prompt
# from tools.product_search_tool import product_search
# from tools.clarifier_tool import clarifier_tool
# from model.chat_model import ChatState
# from config.settings import settings
# from config.llm_config import get_llm
# import json
# from typing import Dict, Any, List
# from langgraph.graph import StateGraph, END
# from prompt.prompts import intent_prompt, response_prompt
# from tools.product_search_tool import product_search
# from tools.clarifier_tool import clarifier_tool
# from model.chat_model import BaseModel

# from config.settings import settings
# from config.llm_config import get_llm




# # ✅ Centralized LLM
# llm = get_llm()

# # -----------------------------
# # NODE: Extract Intent
# # -----------------------------
# async def extract_intent(state: ChatState) -> ChatState:
#     print(f"[Extract Intent] Messages: {state.messages}")
#     try:
#         query = state.messages[-1]["content"]
#         chain = intent_prompt | llm

#         raw_output = chain.invoke({"query": query}).content
#         print(f"[Extract Intent] Raw output: {raw_output}")

#         try:
#             intent = json.loads(raw_output)
#         except json.JSONDecodeError:
#             intent = {"category": None, "plant_type": None, "price_range": None, "quantity": None,
#                       "missing": ["category", "plant_type", "price_range", "quantity"]}

#         state.intent = intent
#         # Only need clarification if missing fields exist and clarification turns are under limit
#         state.needs_clarification = bool(intent.get("missing")) and state.clarification_turn < 2
#         print(f"[Extract Intent] Parsed intent: {intent}")

#     except Exception as e:
#         print(f"❌ Intent extraction error: {str(e)}")
#         state.intent = {"category": None, "plant_type": None, "price_range": None, "quantity": None,
#                         "missing": ["category", "plant_type", "price_range", "quantity"]}
#         state.needs_clarification = True if state.clarification_turn < 2 else False

#     return state
# # -----------------------------
# # NODE: Clarify
# # -----------------------------
# async def clarify(state: ChatState) -> ChatState:
#     state.clarification_turn += 1
#     print(f"💬 Clarify Node (Turn {state.clarification_turn})")

#     if state.clarification_turn > 2:
#         state.clarification_question = "Sorry, I couldn’t understand. Let’s proceed with what we have."
#         state.needs_clarification = False
#         state.messages.append({"role": "assistant", "content": state.clarification_question})
#         return state

#     query = state.messages[-1]["content"]
#     missing = state.intent.get("missing", [])
#     try:
#         clar_question = clarifier_tool.invoke({"query": query, "missing": missing})
#         clar_question = clar_question or "Could you clarify what you're looking for?"
#     except Exception as e:
#         print(f"❌ Clarifier error: {str(e)}")
#         clar_question = "Could you clarify what you're looking for?"

#     state.clarification_question = clar_question
#     state.messages.append({"role": "assistant", "content": clar_question})
#     print(f"[Clarify] Question: {clar_question}")
#     return state
# # -----------------------------
# # NODE: Search Products
# # -----------------------------

# async def search_products(state: ChatState) -> ChatState:
#     intent = state.intent or {}
#     print(f"[Search] Intent: {intent}")
#     category = intent.get("category")
#     price_range = intent.get("price_range")
#     quantity = intent.get("quantity")

#     state.products = []
#     if category:
#         try:
#             state.products = product_search.invoke({
#                 "category": category,
#                 "price_range": price_range,
#                 "quantity": quantity
#             })
#             print(f"[Search] Found {len(state.products)} products")
#         except Exception as e:
#             print(f"❌ Search error: {str(e)}")
#     else:
#         print("[Search] No category provided, returning empty list")

#     return state
# # -----------------------------
# # NODE: Generate Response
# # -----------------------------

# async def generate_response(state: ChatState) -> ChatState:
#     print("📝 Generate Response Node")

#     if state.clarification_question:
#         print("[Generate Response] Waiting for clarification response. Skipping response generation.")
#         return state

#     try:
#         sorted_products = sorted(state.products, key=lambda x: x.get("price", float("inf"))) if state.products else []
#         chain = response_prompt | llm
#         response = chain.invoke({
#             "products_json": json.dumps(sorted_products),
#             "query": state.messages[-1]["content"]
#         }).content

#         if not sorted_products:
#             response = "Sorry, no matches found. Would you like to expand the price range or change the category?"
#         state.messages.append({"role": "assistant", "content": response})
#         print(f"[Generate Response] Response: {response[:200]}...")
#     except Exception as e:
#         print(f"❌ Response generation error: {str(e)}")
#         state.messages.append({"role": "assistant", "content": "Sorry, something went wrong. Please try again."})

#     return state
# # -----------------------------
# # WORKFLOW
# # -----------------------------
# workflow = StateGraph(ChatState)
# workflow.add_node("extract_intent", extract_intent)
# workflow.add_node("clarify", clarify)
# workflow.add_node("search_products", search_products)
# workflow.add_node("generate_response", generate_response)

# async def check_clarification(state: ChatState) -> str:
#     route = "clarify" if state.needs_clarification else "search_products"
#     print(f"[Routing] Decision: {route}")
#     return route

# # Update edges: After clarify, go back to extract_intent only if needed, else proceed
# workflow.add_conditional_edges("extract_intent", check_clarification,
#                                {"clarify": "clarify", "search_products": "search_products"})
# workflow.add_edge("clarify", "extract_intent")  # Re-extract intent after clarification
# workflow.add_edge("search_products", "generate_response")
# workflow.add_edge("generate_response", END)

# workflow.set_entry_point("extract_intent")
# agent_workflow = workflow.compile()
# print("✅ Agent workflow compiled successfully")


import json
from langgraph.graph import StateGraph, END
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.product_search_tool import product_search
from model.chat_model import ChatState
from config.llm_config import get_llm
from config.settings import settings
from prompt.prompts import chat_prompt
import logging

# Set up logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Centralized Gemini LLM
llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=settings.GEMINI_API_KEY, temperature=0.7)

# Define tools
tools = [product_search]

# Create agent
agent = create_openai_tools_agent(llm, tools, chat_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, handle_parsing_errors=True)

# NODE: Agentic Step
async def agent_step(state: ChatState) -> ChatState:
    """
    Agent decides next question or fetches products dynamically based on conversation.
    """
    last_user_message = state.messages[-1]["content"]
    logger.info(f"[Agent] Processing: {last_user_message}")

    try:
        # Prepare LLM input with conversation history
        llm_input = {
            "query": last_user_message,
            "agent_scratchpad": []  # Initial scratchpad for tool calls
        }
        response = await agent_executor.ainvoke(llm_input, config=RunnableConfig(callbacks=[]))

        # Extract the assistant's response
        assistant_response = response.get("output", "Sorry, I couldn’t understand.")
        state.messages.append({"role": "assistant", "content": assistant_response})
        logger.info(f"[Agent] Response: {assistant_response[:200]}...")

        # Check for FETCH_PRODUCTS flag and parse parameters
        if "[FETCH_PRODUCTS]" in assistant_response:
            try:
                # Extract JSON parameters (e.g., {"category": "Tracker", "name_query": "GPS"})
                params_str = assistant_response.split("[FETCH_PRODUCTS]")[1].strip().split("}")[0] + "}"
                params = json.loads(params_str)
                logger.info(f"[Agent] Fetching products with params: {params}")

                # Invoke product_search with parsed parameters
                state.products = product_search.invoke({
                    "category": params.get("category"),
                    "name_query": params.get("name_query"),
                    "description_query": params.get("description_query"),
                    "price_range": params.get("price_range"),
                    "quantity": params.get("quantity")
                })
                logger.info(f"[Agent] Fetched {len(state.products)} products")
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logger.error(f"❌ Product fetch error: {e}")
                state.products = []

    except Exception as e:
        logger.error(f"❌ Agent error: {e}")
        state.messages.append({"role": "assistant", "content": "Sorry, I couldn't process that. Could you rephrase?"})

    return state

# NODE: Generate Response
async def generate_response(state: ChatState) -> ChatState:
    """
    Format and send the final response with products.
    """
    try:
        if state.products:
            sorted_products = sorted(state.products, key=lambda x: x.get("price", float("inf")))
            response = "\n".join([f"📦 {p.get('name', 'Unknown')} — ₹{p.get('price', 0)} — {p.get('imageUrl', '')} — {p.get('description', '')}" for p in sorted_products])
            if len(sorted_products) > 1:
                cheapest = sorted_products[0]
                response += f"\n💰 Cheapest option: {cheapest.get('name', 'Unknown')} at ₹{cheapest.get('price', 0)}"
            response += "\nWould you like to see more options?"
        else:
            response = "Sorry, no matches found. Could you try a different category, name, or price range?"
        state.messages.append({"role": "assistant", "content": response})
        logger.info(f"[Response] Sent: {response[:200]}...")
    except Exception as e:
        logger.error(f"❌ Response generation error: {e}")
        state.messages.append({"role": "assistant", "content": "Sorry, something went wrong."})

    return state

# WORKFLOW
workflow = StateGraph(ChatState)
workflow.add_node("agent_step", agent_step)
workflow.add_node("generate_response", generate_response)

# Workflow edges
workflow.add_edge("agent_step", "generate_response")
workflow.add_edge("generate_response", END)

workflow.set_entry_point("agent_step")
agent_workflow = workflow.compile()
logger.info("✅ Simplified agent workflow compiled successfully")