"""
VitalSense AI - NVIDIA NIM AI Integration Service
Connects to the NVIDIA NIM inference API using the OpenAI-compatible client.
Generates purely informational, educational health remarks based solely on laboratory values.
Never sends patient identifiers. Never diagnoses medical conditions.
"""

import logging
import os
from typing import Optional
from dotenv import load_dotenv
from openai import (
    OpenAI,
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Constants and Configuration
DEFAULT_NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"
DEFAULT_TIMEOUT_SECONDS = 20.0

# System instructions strictly enforcing educational and non-diagnostic boundaries
SYSTEM_PROMPT = (
    "You provide general, educational information about laboratory measurements. "
    "You are not a doctor and must not diagnose diseases, prescribe medication, or claim "
    "that a laboratory value proves a medical condition. Interpret the supplied values "
    "cautiously, taking the supplied units into account. Explain that results depend on "
    "the laboratory reference range and individual clinical context. Identify values that "
    "may warrant discussion with a qualified healthcare professional when appropriate. "
    "Do not invent missing information or make definitive medical conclusions. Keep the "
    "response concise, neutral, and understandable to a general audience. Clearly state "
    "that the output is informational and not a medical diagnosis."
)


class AIServiceError(Exception):
    """Base exception for all AI service operations."""
    pass


class AIConfigurationError(AIServiceError):
    """Raised when NVIDIA API key or model configuration is missing or invalid."""
    pass


class AIAuthenticationError(AIServiceError):
    """Raised when NVIDIA NIM rejects credentials (HTTP 401)."""
    pass


class AIRateLimitError(AIServiceError):
    """Raised when NVIDIA NIM rate limit or quota is exceeded (HTTP 429)."""
    pass


class AITimeoutError(AIServiceError):
    """Raised when request to NVIDIA NIM times out."""
    pass


class AINetworkError(AIServiceError):
    """Raised when connection to NVIDIA NIM API fails."""
    pass


def get_nvidia_config() -> dict:
    """
    Reads NVIDIA configuration from environment variables.
    Does not log or expose the actual API key.
    """
    api_key = os.getenv("NVIDIA_API_KEY", "").strip()
    model = os.getenv("NVIDIA_MODEL", "").strip() or DEFAULT_NVIDIA_MODEL
    base_url = os.getenv("NVIDIA_BASE_URL", "").strip() or DEFAULT_NVIDIA_BASE_URL
    return {
        "api_key": api_key,
        "model": model,
        "base_url": base_url,
    }


def get_openai_client(api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> OpenAI:
    """
    Instantiates an OpenAI client configured for the NVIDIA NIM endpoint.
    """
    config = get_nvidia_config()
    resolved_key = api_key or config["api_key"]
    resolved_base_url = base_url or config["base_url"]

    if not resolved_key or resolved_key in ("your_nvidia_api_key_here", "placeholder"):
        raise AIConfigurationError(
            "NVIDIA API Key is missing or not configured. "
            "Please create a .env file and set NVIDIA_API_KEY with a valid key from https://build.nvidia.com/."
        )

    return OpenAI(
        base_url=resolved_base_url,
        api_key=resolved_key,
        timeout=timeout,
    )


def generate_health_remarks(
    glucose: float, 
    haemoglobin: float, 
    cholesterol: float,
    client: Optional[OpenAI] = None
) -> str:
    """
    Calls NVIDIA NIM inference API to generate educational laboratory remarks.
    
    Privacy Guarantee:
    - Never receives or transmits patient name, DOB, email, or any direct identifiers.
    - Sends solely the numeric laboratory measurements with their standard units.
    
    Arguments:
        glucose: float (mg/dL)
        haemoglobin: float (g/dL)
        cholesterol: float (mg/dL)
        client: Optional[OpenAI] client instance for testing / dependency injection.
        
    Returns:
        str: Informational, non-diagnostic observations from NVIDIA NIM.
        
    Raises:
        AIConfigurationError: Missing or invalid API key
        AIAuthenticationError: Invalid NVIDIA API key
        AIRateLimitError: Quota or rate limit exceeded
        AITimeoutError: Connection timed out
        AINetworkError: Network connection error
        AIServiceError: Unexpected API response or validation failure
    """
    config = get_nvidia_config()
    model = config["model"]

    # Minimum necessary payload: only laboratory values and units
    user_prompt = (
        f"Please provide concise, educational informational observations for these laboratory measurements:\n"
        f"- Blood Glucose: {glucose:.1f} mg/dL\n"
        f"- Haemoglobin: {haemoglobin:.1f} g/dL\n"
        f"- Total Cholesterol: {cholesterol:.1f} mg/dL\n\n"
        f"Remember: Do not diagnose conditions or prescribe medications. Provide general educational context only."
    )

    if client is None:
        client = get_openai_client()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=500,
        )
    except AuthenticationError as e:
        logger.error("NVIDIA NIM authentication failed: Invalid or expired API key.")
        raise AIAuthenticationError(
            "NVIDIA NIM authentication failed. Please verify that your NVIDIA_API_KEY in .env is valid."
        ) from e
    except RateLimitError as e:
        logger.error("NVIDIA NIM rate limit or credit limit reached.")
        raise AIRateLimitError(
            "NVIDIA NIM rate limit or quota exceeded. Please wait a moment before trying again."
        ) from e
    except APITimeoutError as e:
        logger.error("NVIDIA NIM request timed out after %.1f seconds.", DEFAULT_TIMEOUT_SECONDS)
        raise AITimeoutError(
            "The AI service timed out while generating health remarks. Please check your network and retry."
        ) from e
    except APIConnectionError as e:
        logger.error("Failed to connect to NVIDIA NIM API endpoint.")
        raise AINetworkError(
            "Unable to connect to NVIDIA NIM API. Please check your internet connection."
        ) from e
    except APIError as e:
        logger.error("NVIDIA NIM returned an API error: %s", str(e))
        raise AIServiceError(f"NVIDIA API Error: {str(e)}") from e
    except Exception as e:
        logger.error("Unexpected error during AI generation: %s", str(e))
        raise AIServiceError(f"An unexpected error occurred during AI processing: {str(e)}") from e

    # Validate response structure and content
    if not response or not response.choices:
        raise AIServiceError("NVIDIA NIM returned an empty response with no choices.")

    content = response.choices[0].message.content
    if not content or not content.strip():
        raise AIServiceError("NVIDIA NIM returned an empty or whitespace response.")

    cleaned_remarks = content.strip()

    # Plausibility limit on response length to prevent corrupted buffer issues
    if len(cleaned_remarks) > 4000:
        raise AIServiceError("AI response exceeded allowable length threshold.")

    return cleaned_remarks
