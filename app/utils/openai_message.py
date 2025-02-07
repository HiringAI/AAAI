class OpenAIMessage():
    def __init__(self):
        self._system_message = ""
        self._user_messages = []

    def set_system_message(self, content):
        self._system_message = content

    def add_user_message(self, message_type, content):
        if message_type == "text":
            self._user_messages.append({
                "type": "text",
                "text": content
            })
        elif message_type == "image_url":
            self._user_messages.append({
                "type": "image_url",
                "image_url": {
                    "url": content
                }
            })
        else:
            raise ValueError("Invalid message type")

    def get_messages(self):
        return [
            {"role": "system", "content": self._system_message},
            {"role": "user", "content": self._user_messages}
        ]