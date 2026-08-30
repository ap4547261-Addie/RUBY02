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
        self.cloud_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

    def _is_connected(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            return False

    def route_request(self, messages, personality=None, use_cloud_preferred=True):
        if use_cloud_preferred and self.cloud_api_key:
            max_retries = 3
            backoff_delay = 3
            
            for attempt in range(max_retries):
                try:
                    response = self._call_cloud(messages, personality)
                    if response:
                        return {"source": "cloud", "response": response}
                except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout) as e:
                    status_code = getattr(e, 'code', None)
                    if status_code in [429, 503] or isinstance(e, (socket.timeout, urllib.error.URLError)):
                        if attempt < max_retries - 1:
                            print(f"Network glitch ({e}). Retrying in {backoff_delay}s... (Attempt {attempt + 1}/{max_retries})")
                            time.sleep(backoff_delay)
                            backoff_delay *= 2
                            continue
                    return {"source": "local", "response": f"Cloud Error: {str(e)}"}
                except Exception as e:
                    return {"source": "local", "response": f"Cloud Error: {str(e)}"}

        return {"source": "local", "response": self._call_local(messages)}

    def _call_cloud(self, messages, personality=None):
        gemini_contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        url = f"{self.cloud_url}?key={self.cloud_api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": gemini_contents}
        
        if personality:
            payload["system_instruction"] = {
                "parts": [{"text": personality}]
            }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=25) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["candidates"][0]["content"]["parts"][0]["text"]

    def _call_local(self, messages):
        if self.local_model_path:
            pass
        return "Error: API Key missing or cloud request failed."
