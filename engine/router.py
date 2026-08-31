# engine/router.py
import os
import urllib.request
import urllib.error
import json
import socket
import time


class BrainRouter:
    def __init__(self, cloud_api_key=None, local_model_path=None):
        self.cloud_api_key = cloud_api_key or os.getenv("GEMINI_API_KEY")
        self.local_model_path = local_model_path

        self.cloud_url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-3.7-flash:generateContent"
        )

    def _is_connected(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            return False

    def route_request(
        self,
        messages,
        personality=None,
        use_cloud_preferred=True
    ):
        if use_cloud_preferred and self.cloud_api_key:
            max_retries = 3
            backoff_delay = 3

            for attempt in range(max_retries):
                try:
                    response = self._call_cloud(
                        messages,
                        personality
                    )

                    if response:
                        return {
                            "source": "cloud",
                            "response": response
                        }

                except urllib.error.HTTPError as e:
                    status_code = e.code

                    try:
                        error_message = e.read().decode("utf-8")
                    except Exception:
                        error_message = str(e)

                    # Never retry quota exhaustion.
                    if status_code == 429:
                        print(
                            "Gemini quota/rate limit reached. "
                            "No automatic retry."
                        )

                        return {
                            "source": "quota",
                            "response": (
                                "My cloud brain is temporarily "
                                "out of requests."
                            )
                        }

                    # Retry temporary server problems.
                    if status_code == 503:
                        if attempt < max_retries - 1:
                            print(
                                f"Gemini temporarily unavailable. "
                                f"Retrying in {backoff_delay}s..."
                            )
                            time.sleep(backoff_delay)
                            backoff_delay *= 2
                            continue

                    return {
                        "source": "cloud_error",
                        "response": f"Cloud Error: {error_message}"
                    }

                except (
                    urllib.error.URLError,
                    socket.timeout
                ) as e:

                    if attempt < max_retries - 1:
                        print(
                            f"Network error: {e}. "
                            f"Retrying in {backoff_delay}s..."
                        )

                        time.sleep(backoff_delay)
                        backoff_delay *= 2
                        continue

                    return {
                        "source": "network_error",
                        "response": f"Network Error: {e}"
                    }

                except Exception as e:
                    return {
                        "source": "cloud_error",
                        "response": f"Cloud Error: {e}"
                    }

        return {
            "source": "local",
            "response": self._call_local(messages)
        }

    def _call_cloud(self, messages, personality=None):
        gemini_contents = []
        system_instruction = personality

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            # Properly extract system instructions.
            if role == "system":
                if system_instruction:
                    system_instruction += "\n\n" + content
                else:
                    system_instruction = content

                continue

            # Gemini accepts user/model conversation roles.
            if role not in ("user", "model"):
                continue

            gemini_contents.append({
                "role": role,
                "parts": [
                    {
                        "text": content
                    }
                ]
            })

        payload = {
            "contents": gemini_contents
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [
                    {
                        "text": system_instruction
                    }
                ]
            }

        url = f"{self.cloud_url}?key={self.cloud_api_key}"

        headers = {
            "Content-Type": "application/json"
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(
            req,
            timeout=25
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        candidates = result.get("candidates", [])

        if not candidates:
            raise RuntimeError(
                f"Gemini returned no candidates: {result}"
            )

        parts = candidates[0].get("content", {}).get("parts", [])

        text_parts = [
            part.get("text", "")
            for part in parts
            if part.get("text")
        ]

        if not text_parts:
            raise RuntimeError(
                f"Gemini returned no text: {result}"
            )

        return "\n".join(text_parts)

    def _call_local(self, messages):
        if self.local_model_path:
            # Local model integration will go here later.
            pass

        return (
            "Ruby's local brain is not connected yet."
        )
