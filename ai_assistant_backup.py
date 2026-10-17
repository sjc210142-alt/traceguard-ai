import json
import urllib.request
import urllib.error


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2"


def generate_investigation_report(transaction, shared_devices=None):
    """
    Generate an investigation report using actual transaction data.

    transaction: Dictionary containing transaction details.
    shared_devices: Optional list of related accounts or devices.
    """

    if not isinstance(transaction, dict):
        return "Error: Transaction details must be provided as a dictionary."

    if shared_devices is None:
        shared_devices = []

    investigation_data = {
        "transaction": transaction,
        "related_accounts_and_devices": shared_devices,
    }

    prompt = f"""
You are TraceGuard AI, an assistant for financial fraud investigators.

Analyze the following supplied investigation data:

{json.dumps(investigation_data, indent=2, default=str)}

Write a report with these sections:
1. Transaction Summary
2. Observed Risk Indicators
3. Related Accounts and Devices
4. Recommended Investigation Steps
5. Limitations and Uncertainties

IMPORTANT RULES:
- Use only the supplied facts.
- Never invent missing transaction details.
- Clearly distinguish observed facts from possible concerns.
- A shared device alone does not prove fraud.
- A risk score is an indicator, not proof of criminal activity.
- If information is missing, state that it was not provided.
- Recommend human review before any consequential decision.
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))

        return result["message"]["content"]

    except urllib.error.URLError as error:
        return (
            "Could not connect to Ollama. "
            "Make sure Ollama is running and the model is available. "
            f"Details: {error}"
        )

    except (KeyError, json.JSONDecodeError) as error:
        return f"Could not read the AI response: {error}"

    except TimeoutError:
        return "The AI request timed out. Please try again."