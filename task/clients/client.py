import os
from aidial_client import Dial, AsyncDial

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT, API_KEY
from task.models.conversation import Conversation
from task.models.message import Message
from task.models.role import Role

class DialClient(BaseClient):
    _endpoint: str

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        #TODO:
        # Documentation: https://pypi.org/project/aidial-client/ (here you can find how to create and use these clients)
        # 1. Create Dial client
        # 2. Create AsyncDial client
        self._endpoint = DIAL_ENDPOINT
        self.dial_client = Dial(api_key=API_KEY, base_url=self._endpoint)
        self.async_dial_client = AsyncDial(
            api_key=API_KEY, base_url=self._endpoint
        )

    def get_completion(self, messages: list[Message] | Conversation) -> Message:
        #TODO:
        # 1. Create chat completions with client
        #    Hint: to unpack messages you can use the `to_dict()` method from Message object
        # 2. Get content from response, print it and return message with assistant role and content
        # 3. If choices are not present then raise Exception("No choices in response found")
        if isinstance(messages, Conversation):
            messages = messages.get_messages()
        
        response = self.dial_client.chat.completions.create(
            deployment_name=self._deployment_name,
            stream=False,
            messages=[msg.to_dict() for msg in messages]
        )
        
        if not response.choices:
            raise Exception("No choices in response found")
        
        content = response.choices[0].message.content
        
        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message] | Conversation) -> Message:
        #TODO:
        # 1. Create chat completions with async client
        #    Hint: don't forget to add `stream=True` in call.
        # 2. Create array with `contents` name (here we will collect all content chunks)
        # 3. Make async loop from `chunks` (from 1st step)
        # 4. Print content chunk and collect it contents array
        # 5. Print empty row `print()` (it will represent the end of streaming and in console we will print input from a new line)
        # 6. Return Message with assistant role and message collected content
        if isinstance(messages, Conversation):
            messages = messages.get_messages()
        
        response = await self.async_dial_client.chat.completions.create(
            deployment_name=self._deployment_name,
            stream=True,
            messages=[msg.to_dict() for msg in messages]
        )
        
        contents = []
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                contents.append(content)
          
        return Message(role=Role.AI, content="".join(contents))
