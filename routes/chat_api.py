# # from __future__ import annotations
# # import json
# # import time
# # from typing import Dict, Any, Optional
# # from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
# # from firebase_admin import auth as fb_auth
# # from pydantic import ValidationError
# # from model.chat_model import ChatState
# # from model.user_response import UserQuery
# # from agent.agent_setup import agent_workflow
# # import asyncio

# # # Config
# # PING_INTERVAL_SEC = 25          # Heartbeat ping interval
# # MAX_MESSAGE_BYTES = 64 * 1024   # 64KB message size limit
# # MAX_MESSAGES_PER_MIN = 120      # Rate limit per connection
# # CONNECTION_TIMEOUT_SEC = 60     # Auth window

# # router = APIRouter()


# # def _json_sendable(data: Dict[str, Any]) -> str:
# #     """Safe JSON dump with emoji support."""
# #     return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


# # def _now() -> float:
# #     return time.time()


# # async def _recv_text_safely(ws: WebSocket) -> str:
# #     """Receive text with size guard."""
# #     text = await ws.receive_text()
# #     if len(text.encode("utf-8")) > MAX_MESSAGE_BYTES:
# #         raise ValueError("Message too large")
# #     return text


# # def _extract_token(websocket: WebSocket) -> Optional[str]:
# #     """Extract Firebase ID token from query param or Authorization header."""
# #     token = websocket.query_params.get("token")
# #     if token:
# #         return token
# #     auth_hdr = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
# #     if auth_hdr and auth_hdr.lower().startswith("bearer "):
# #         return auth_hdr.split(" ", 1)[1].strip()
# #     return None


# # async def _send_ping(ws: WebSocket):
# #     """Send heartbeat ping every PING_INTERVAL_SEC seconds."""
# #     while True:
# #         await asyncio.sleep(PING_INTERVAL_SEC)
# #         try:
# #             await ws.send_text(_json_sendable({"type": "ping", "ts": int(_now())}))
# #         except Exception:
# #             break  # Connection closed


# # @router.websocket("/ws/chat")
# # async def ws_chat(websocket: WebSocket):
# #     await websocket.accept()
    
# #     # Authenticate with Firebase
# #     try:
# #         token = _extract_token(websocket)
# #         if not token:
# #             await websocket.send_text(_json_sendable({
# #                 "type": "error",
# #                 "code": "auth/missing-token",
# #                 "message": "Missing Firebase ID token. Pass ?token=ID_TOKEN or Authorization: Bearer ID_TOKEN."
# #             }))
# #             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
# #             return
        
# #         # ✅ Decode and print token info for debugging
# #         decoded = fb_auth.verify_id_token(token, clock_skew_seconds=30)
# #         print("Decoded Firebase token:", decoded)
# #         user_uid = decoded.get("uid")
# #         if not user_uid:
# #             raise ValueError("Invalid token: missing uid")
        
# #         await websocket.send_text(_json_sendable({
# #             "type": "system",
# #             "message": "Connected.",
# #             "uid": user_uid
# #         }))
# #     except Exception as e:
# #         print("Authentication failed:", e)
# #         await websocket.send_text(_json_sendable({
# #             "type": "error",
# #             "code": "auth/invalid-token",
# #             "message": f"Authentication failed: {str(e)}"
# #         }))
# #         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
# #         return

# #     # Initialize connection state
# #     state = ChatState(messages=[])
# #     msg_count = 0
# #     window_start = _now()

# #     # Start heartbeat in background
# #     asyncio.create_task(_send_ping(websocket))

# #     try:
# #         while True:
# #             # Rate limiting
# #             if _now() - window_start >= 60:
# #                 window_start = _now()
# #                 msg_count = 0

# #             # Receive and parse message
# #             raw_text = await _recv_text_safely(websocket)
# #             msg_count += 1
# #             if msg_count > MAX_MESSAGES_PER_MIN:
# #                 await websocket.send_text(_json_sendable({
# #                     "type": "error",
# #                     "code": "rate/too-many-requests",
# #                     "message": "Too many messages. Slow down and try again."
# #                 }))
# #                 await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
# #                 return

# #             # Parse with UserQuery model
# #             try:
# #                 payload = json.loads(raw_text)
# #                 user_query = UserQuery(**payload)
# #                 user_text = user_query.message.strip()
# #                 if not user_text:
# #                     await websocket.send_text(_json_sendable({
# #                         "type": "error",
# #                         "code": "protocol/empty-content",
# #                         "message": "Message cannot be empty."
# #                     }))
# #                     continue
# #                 print(f"Received query: {user_text}")
# #             except ValidationError as e:
# #                 await websocket.send_text(_json_sendable({
# #                     "type": "error",
# #                     "code": "protocol/invalid-json",
# #                     "message": f"Invalid message format: {str(e)}"
# #                 }))
# #                 continue
# #             except json.JSONDecodeError as e:
# #                 await websocket.send_text(_json_sendable({
# #                     "type": "error",
# #                     "code": "protocol/bad-json",
# #                     "message": f"Invalid JSON: {str(e)}"
# #                 }))
# #                 continue

# #             # Run LangGraph agent
# #             try:
# #                 state.messages.append({"role": "user", "content": user_text})
# #                 result: ChatState = await agent_workflow.ainvoke(state)
# #                 assistant_msg = result.messages[-1]["content"] if result.messages else ""
# #                 resp = {
# #                     "type": "assistant_message",
# #                     "content": assistant_msg,
# #                     "intent": result.intent or {},
# #                     "products": result.products or [],
# #                     "clarification_question": result.clarification_question or ""
# #                 }
# #                 print(f"Sending response: {assistant_msg}")
# #                 await websocket.send_text(_json_sendable(resp))
# #                 state = result
# #             except Exception as e:
# #                 print(f"Agent error: {str(e)}")
# #                 await websocket.send_text(_json_sendable({
# #                     "type": "error",
# #                     "code": "agent/failure",
# #                     "message": "Sorry, something went wrong. Please try again."
# #                 }))

# #     except WebSocketDisconnect:
# #         print("WebSocket disconnected")
# #         return
# #     except Exception as e:
# #         print(f"WebSocket error: {str(e)}")
# #         try:
# #             await websocket.send_text(_json_sendable({
# #                 "type": "error",
# #                 "code": "ws/internal",
# #                 "message": "Unexpected error. Closing connection."
# #             }))
# #         finally:
# #             await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

# from __future__ import annotations
# import json
# import time
# from typing import Dict, Any, Optional
# from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
# from pydantic import ValidationError
# from model.chat_model import ChatState
# from model.user_response import UserQuery
# from agent.agent_setup import agent_workflow
# import asyncio

# # Config
# PING_INTERVAL_SEC = 25          # Heartbeat ping interval
# MAX_MESSAGE_BYTES = 64 * 1024   # 64KB message size limit
# MAX_MESSAGES_PER_MIN = 120      # Rate limit per connection

# router = APIRouter()


# def _json_sendable(data: Dict[str, Any]) -> str:
#     """Safe JSON dump with emoji support."""
#     return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


# def _now() -> float:
#     return time.time()


# async def _recv_text_safely(ws: WebSocket) -> str:
#     """Receive text with size guard."""
#     text = await ws.receive_text()
#     if len(text.encode("utf-8")) > MAX_MESSAGE_BYTES:
#         raise ValueError("Message too large")
#     return text


# async def _send_ping(ws: WebSocket):
#     """Send heartbeat ping every PING_INTERVAL_SEC seconds."""
#     while True:
#         await asyncio.sleep(PING_INTERVAL_SEC)
#         try:
#             await ws.send_text(_json_sendable({"type": "ping", "ts": int(_now())}))
#         except Exception:
#             break  # Connection closed


# @router.websocket("/ws/chat")
# async def ws_chat(websocket: WebSocket):
#     await websocket.accept()
#     print("✅ WebSocket connection accepted")

#     # Initialize connection state
#     state = ChatState(messages=[])
#     msg_count = 0
#     window_start = _now()

#     # Start heartbeat in background
#     asyncio.create_task(_send_ping(websocket))

#     try:
#         while True:
#             # Rate limiting
#             if _now() - window_start >= 60:
#                 window_start = _now()
#                 msg_count = 0

#             # Receive and parse message
#             raw_text = await _recv_text_safely(websocket)
#             msg_count += 1
#             if msg_count > MAX_MESSAGES_PER_MIN:
#                 await websocket.send_text(_json_sendable({
#                     "type": "error",
#                     "code": "rate/too-many-requests",
#                     "message": "Too many messages. Slow down and try again."
#                 }))
#                 await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
#                 return

#             # Parse with UserQuery model
#             try:
#                 payload = json.loads(raw_text)
#                 user_query = UserQuery(**payload)
#                 user_text = user_query.message.strip()
#                 if not user_text:
#                     await websocket.send_text(_json_sendable({
#                         "type": "error",
#                         "code": "protocol/empty-content",
#                         "message": "Message cannot be empty."
#                     }))
#                     continue
#                 print(f"[Received] User query: {user_text}")
#             except ValidationError as e:
#                 await websocket.send_text(_json_sendable({
#                     "type": "error",
#                     "code": "protocol/invalid-json",
#                     "message": f"Invalid message format: {str(e)}"
#                 }))
#                 continue
#             except json.JSONDecodeError as e:
#                 await websocket.send_text(_json_sendable({
#                     "type": "error",
#                     "code": "protocol/bad-json",
#                     "message": f"Invalid JSON: {str(e)}"
#                 }))
#                 continue

#             # Run LangGraph agent
#             try:
#                 # Append user message to state
#                 state.messages.append({"role": "user", "content": user_text})
#                 print(f"[State] Messages before agent invocation: {state.messages}")

#                 # Invoke agent workflow
#                 result = await agent_workflow.ainvoke(state)
#                 print(f"[Agent] Raw result type: {type(result)}")

#                 # Ensure result is ChatState
#                 if not isinstance(result, ChatState):
#                     print("[Agent] Converting dict to ChatState")
#                     result = ChatState(**result)

#                 print(f"[Agent] Messages after agent invocation: {result.messages}")
#                 assistant_msg = result.messages[-1]["content"] if result.messages else ""

#                 # Prepare response
#                 resp = {
#                     "type": "assistant_message",
#                     "content": assistant_msg,
#                     "intent": result.intent or {},
#                     "products": result.products or [],
#                     "clarification_question": result.clarification_question or ""
#                 }
#                 print(f"[Sending] Response: {assistant_msg}")

#                 await websocket.send_text(_json_sendable(resp))

#                 # Update state for next turn
#                 state = result

#             except Exception as e:
#                 print(f"[Agent ERROR] {str(e)}")
#                 await websocket.send_text(_json_sendable({
#                     "type": "error",
#                     "code": "agent/failure",
#                     "message": "Sorry, something went wrong. Please try again."
#                 }))

#     except WebSocketDisconnect:
#         print("⚠️ WebSocket disconnected")
#         return
#     except Exception as e:
#         print(f"[WebSocket ERROR] {str(e)}")
#         try:
#             await websocket.send_text(_json_sendable({
#                 "type": "error",
#                 "code": "ws/internal",
#                 "message": "Unexpected error. Closing connection."
#             }))
#         finally:
#             await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


from __future__ import annotations
import json
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError
from model.chat_model import ChatState
from model.user_response import UserQuery
from agent.agent_setup import agent_workflow
import asyncio

# Config
PING_INTERVAL_SEC = 25          # Heartbeat ping interval
MAX_MESSAGE_BYTES = 64 * 1024   # 64KB message size limit
MAX_MESSAGES_PER_MIN = 120      # Rate limit per connection

router = APIRouter()

def _json_sendable(data: Dict[str, Any]) -> str:
    """Safe JSON dump with emoji support."""
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

def _now() -> float:
    return time.time()

async def _recv_text_safely(ws: WebSocket) -> str:
    """Receive text with size guard."""
    text = await ws.receive_text()
    if len(text.encode("utf-8")) > MAX_MESSAGE_BYTES:
        raise ValueError("Message too large")
    return text

async def _send_ping(ws: WebSocket):
    """Send heartbeat ping every PING_INTERVAL_SEC seconds."""
    while True:
        await asyncio.sleep(PING_INTERVAL_SEC)
        try:
            await ws.send_text(_json_sendable({"type": "ping", "ts": int(_now())}))
        except Exception:
            break  # Connection closed

@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    print("✅ WebSocket connection accepted")

    # Initialize connection state
    state = ChatState(messages=[])
    msg_count = 0
    window_start = _now()

    # Start heartbeat in background
    asyncio.create_task(_send_ping(websocket))

    try:
        while True:
            # Rate limiting
            if _now() - window_start >= 60:
                window_start = _now()
                msg_count = 0

            # Receive and parse message
            raw_text = await _recv_text_safely(websocket)
            msg_count += 1
            if msg_count > MAX_MESSAGES_PER_MIN:
                await websocket.send_text(_json_sendable({
                    "type": "error",
                    "code": "rate/too-many-requests",
                    "message": "Too many messages. Slow down and try again."
                }))
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
                return

            # Parse with UserQuery model
            try:
                payload = json.loads(raw_text)
                user_query = UserQuery(**payload)
                user_text = user_query.message.strip()
                if not user_text:
                    await websocket.send_text(_json_sendable({
                        "type": "error",
                        "code": "protocol/empty-content",
                        "message": "Message cannot be empty."
                    }))
                    continue
                print(f"[Received] User query: {user_text}")
            except ValidationError as e:
                await websocket.send_text(_json_sendable({
                    "type": "error",
                    "code": "protocol/invalid-json",
                    "message": f"Invalid message format: {str(e)}"
                }))
                continue
            except json.JSONDecodeError as e:
                await websocket.send_text(_json_sendable({
                    "type": "error",
                    "code": "protocol/bad-json",
                    "message": f"Invalid JSON: {str(e)}"
                }))
                continue

            # Run agent workflow
            try:
                state.messages.append({"role": "user", "content": user_text})
                result = await agent_workflow.ainvoke(state)
                assistant_msg = result.messages[-1]["content"] if result.messages else ""
                resp = {
                    "type": "assistant_message",
                    "content": assistant_msg,
                    "products": result.products or []
                }
                print(f"[Sending] Response: {assistant_msg}")
                await websocket.send_text(_json_sendable(resp))
                state = result
            except Exception as e:
                print(f"[Agent ERROR] {str(e)}")
                await websocket.send_text(_json_sendable({
                    "type": "error",
                    "code": "agent/failure",
                    "message": "Sorry, something went wrong. Please try again."
                }))

    except WebSocketDisconnect:
        print("⚠️ WebSocket disconnected")
        return
    except Exception as e:
        print(f"[WebSocket ERROR] {str(e)}")
        try:
            await websocket.send_text(_json_sendable({
                "type": "error",
                "code": "ws/internal",
                "message": "Unexpected error. Closing connection."
            }))
        finally:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)