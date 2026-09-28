from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from google.genai import types, errors
from dotenv import load_dotenv
from typing import Literal
import os
import time

from api_services import get_weather


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured."
    )


MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.1-flash-lite"
)

client = genai.Client(
    api_key=api_key
)


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Nova AI Assistant Cloud API",
    description="Cloud backend for Nova AI Desktop Assistant",
    version="1.0.0"
)


# =========================================================
# REQUEST MODELS
# =========================================================

class ChatRequest(BaseModel):
    message: str


class CommandRequest(BaseModel):
    message: str


class CommandIntent(BaseModel):

    action: Literal[
        "open_youtube",
        "search_youtube",
        "open_google",
        "search_google",
        "open_gmail",

        "open_calculator",
        "close_calculator",
        "open_notepad",
        "open_file_explorer",
        "close_file_explorer",
        "open_task_manager",
        "open_command_prompt",
        "open_settings",

        "open_desktop",
        "open_documents",
        "open_downloads",

        "create_folder",
        "create_text_file",

        "get_time",
        "get_date",
        "get_battery",
        "get_ram",
        "get_cpu",
        "get_system_info",

        "take_screenshot",

        "volume_up",
        "volume_down",
        "volume_mute",
        "get_volume",

        "brightness_up",
        "brightness_down",
        "get_brightness",

        "play_pause",
        "next_song",
        "previous_song",

        "lock_computer",
        "shutdown_computer",
        "restart_computer",

        "get_weather",

        "unknown"
    ]

    query: str = ""


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
def home():

    return {
        "status": "success",
        "message": "Nova Cloud API is running."
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "Nova Cloud API"
    }


# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
def chat(request: ChatRequest):

    last_error = None

    for _ in range(3):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=request.message
            )

            return {
                "status": "success",
                "response": response.text
            }

        except errors.APIError as e:

            last_error = str(e)

            if "503" in str(e):

                time.sleep(2)

            else:

                break

        except Exception as e:

            last_error = str(e)
            break

    return {
        "status": "error",
        "message": "AI service temporarily unavailable.",
        "details": last_error
    }


# =========================================================
# SMART COMMAND
# =========================================================

@app.post("/smart-command")
def smart_command(request: CommandRequest):

    prompt = f"""
You are Nova, a cloud AI assistant that controls a user's
Windows laptop through a separate local agent.

Return exactly one supported action.

SUPPORTED ACTIONS:

WEBSITES:
- open_youtube
- search_youtube
- open_google
- search_google
- open_gmail

APPLICATIONS:
- open_calculator
- close_calculator
- open_notepad
- open_file_explorer
- close_file_explorer
- open_task_manager
- open_command_prompt
- open_settings

FOLDERS:
- open_desktop
- open_documents
- open_downloads

FILES:
- create_folder
- create_text_file

SYSTEM:
- get_time
- get_date
- get_battery
- get_ram
- get_cpu
- get_system_info

SCREENSHOT:
- take_screenshot

VOLUME:
- volume_up
- volume_down
- volume_mute
- get_volume

BRIGHTNESS:
- brightness_up
- brightness_down
- get_brightness

MEDIA:
- play_pause
- next_song
- previous_song

COMPUTER:
- lock_computer
- shutdown_computer
- restart_computer

WEATHER:
- get_weather

UNKNOWN:
- unknown

RULES:
- Choose exactly one action.
- Never invent an action.
- For searches, put the search topic in query.
- For create_folder, put only the folder name in query.
- For create_text_file, put only the filename in query.
- For get_weather, put only the city name in query.
- For actions that need no query, query must be empty.
- Never generate shell commands.

USER REQUEST:
{request.message}
"""

    last_error = None

    for _ in range(3):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CommandIntent
                )
            )

            intent = response.parsed

            if intent is None:

                return {
                    "status": "error",
                    "message": "Nova could not understand the request."
                }

            # -------------------------------------------------
            # WEATHER IS HANDLED BY CLOUD
            # -------------------------------------------------

            if intent.action == "get_weather":

                weather = get_weather(
                    intent.query
                )

                if not weather.get("success"):

                    return {
                        "status": "error",
                        "source": "weather_api",
                        "message": weather.get(
                            "message",
                            "Weather service failed."
                        )
                    }

                return {
                    "status": "success",
                    "source": "weather_api",
                    "action": "get_weather",
                    "query": intent.query,
                    "response": (
                        f"The weather in "
                        f"{weather['city']} is "
                        f"{weather['description']} at "
                        f"{weather['temperature']}°C. "
                        f"It feels like "
                        f"{weather['feels_like']}°C."
                    ),
                    "weather": weather
                }

            # -------------------------------------------------
            # RETURN ACTION TO LOCAL AGENT
            # -------------------------------------------------

            if intent.action == "unknown":

                return {
                    "status": "unknown",
                    "action": "unknown",
                    "response":
                        "I don't know how to perform that task yet."
                }

            return {
                "status": "success",
                "source": "cloud_ai",
                "action": intent.action,
                "query": intent.query,
                "response":
                    "Action identified successfully."
            }

        except errors.APIError as e:

            last_error = str(e)

            if "503" in str(e):

                time.sleep(2)

            else:

                break

        except Exception as e:

            last_error = str(e)
            break

    return {
        "status": "error",
        "message": "Cloud AI service is temporarily unavailable.",
        "details": last_error
    }