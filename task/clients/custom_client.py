import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT, API_KEY
from task.models.conversation import Conversation
from task.models.message import Message
from task.models.role import Role


class DialClient:
    _endpoint: str
    _api_key: str

    def __init__(self, deployment_name: str):
        self._endpoint = DIAL_ENDPOINT + f"/openai/deployments/{deployment_name}/chat/completions"
        self._api_key = API_KEY

    def get_completion(self, messages: list[Message] | Conversation) -> Message:
        #TODO:
        # Take a look at README.md of how the request and regular response are looks like!
        # 1. Create headers dict with api-key and Content-Type
        # 2. Create request_data dictionary with:
        #   - "messages": convert messages list to dict format using msg.to_dict() for each message
        # 3. Make POST request using requests.post() with:
        #   - URL: self._endpoint
        #   - headers: headers from step 1
        #   - json: request_data from step 2
        # 4. Get content from response, print it and return message with assistant role and content
        # 5. If status code != 200 then raise Exception with format: f"HTTP {response.status_code}: {response.text}"

        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json",
        }

        if isinstance(messages, Conversation):
            messages = messages.get_messages()

        # 2. Create request_data dictionary
        request_data = {
            "stream": False,
            "messages": [msg.to_dict() for msg in messages],
        }
        
        # 3. Make POST request
        response = requests.post(
            self._endpoint,
            headers=headers,
            json=request_data,
            timeout=15,
        )
        
        # 5. Check status code
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        
        # 4. Get content from response and return message
        content = response.json()["choices"][0]["message"]["content"]
        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message] | Conversation) -> Message:
        #TODO:
        # Take a look at README.md of how the request and streamed response chunks are looks like!
        # 1. Create headers dict with api-key and Content-Type
        # 2. Create request_data dictionary with:
        #    - "stream": True  (enable streaming)
        #    - "messages": convert messages list to dict format using msg.to_dict() for each message
        # 3. Create empty list called 'contents' to store content snippets
        # 4. Create aiohttp.ClientSession() using 'async with' context manager
        # 5. Inside session, make POST request using session.post() with:
        #    - URL: self._endpoint
        #    - json: request_data from step 2
        #    - headers: headers from step 1
        #    - Use 'async with' context manager for response
        # 6. Get content from chunks (don't forget that chunk start with `data: `, final chunk is `data: [DONE]`), print
        #    chunks, collect them and return as assistant message
      
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json",
        }

        if isinstance(messages, Conversation):
            messages = messages.get_messages()

        request_data = {
            "stream": True,
            "messages": [msg.to_dict() for msg in messages],
        }
        
        contents = []
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self._endpoint,
                json=request_data,
                headers=headers,
            ) as response:
                async for raw in response.content.iter_any():
                    if not raw:
                        continue

                    try:
                        text = raw.decode("utf-8")
                    except Exception:
                        continue

                    for line in text.splitlines():
                        payload = line[len("data: "):].strip() if line.startswith("data: ") else line.strip()
                        if not payload or payload == "[DONE]":
                            continue

                        try:
                            parsed = __import__("json").loads(payload)
                        except Exception:
                            continue

                        choice = (parsed.get("choices") or [{}])[0]
                        delta = (choice.get("delta") or {}).get("content")
                        content = delta if delta is not None else (choice.get("message") or {}).get("content")
                        if content:
                            contents.append(content)
        
        full_content = ''.join(contents)
        return Message(role=Role.AI, content=full_content)

