import os
import urllib.request
import json
import socket

class BrainRouter:
    def __init__(self, cloud_api_key=None, local_model_path=None):
        self.cloud_api_key = cloud_api_key or os.getenv("GEMINI_API_KEY")
        self.local_model_path = local_model_path
        self.cloud_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def _is_connected(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            return False

    def route_request(self, messages, use_cloud_preferred=True):
        if use_cloud_preferred and self.cloud_api_key:
            try:
                response = self._call_cloud(messages)
                if response:
                    return {"source": "cloud", "response": response}
            except Exception as e:
                print(f"Cloud model failed ({e}).")
                return {"source": "local", "response": f"Cloud Error: {str(e)}"}

        return {"source": "local", "response": self._call_local(messages)}

    def _call_cloud(self, messages):
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
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
                
        except socket.timeout:
            print("GEMINI FLASH API TIMED OUT.")
            raise Exception("Cloud request timed out. The server took too long to respond.")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            print(f"GEMINI FLASH API FAILED WITH CODE {e.code}: {error_body}")
            raise e

    def _call_local(self, messages):
        if self.local_model_path:
            pass
        return "Error: API Key missing or cloud request failed. Check your configuration secrets!"
        
