from collections import defaultdict
from contextlib import contextmanager
from typing import Text, Dict, List, Generator
import math
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

inmemory_storage = defaultdict(list)


class Conversation(object):
    def __init__(
        self, conversation_id: Text, old_conversation_events: List[Dict]
    ) -> None:
        """Creates a conversation.

        Args:
            old_conversation_events: Events which happened earlier in this conversation.
        """
        self.conversation_id = conversation_id
        self.conversation_events = old_conversation_events
        self.number_old_events = len(old_conversation_events)

    """
    1. change method name to add_user_message
    """
    def addd_user_message(self, message: Text) -> None:
        self.conversation_events.append({"type": "user", "message": message})

    def add_bot_message(self, bot_messages: Text) -> None:
        self.conversation_events.append({"type": "bot", "message": bot_messages})

    def new_events_dict(self) -> List[Dict]:
        return self.conversation_events[self.number_old_events :]

"""
All names shall follow snake case in conversation_persistence
"""
@contextmanager
def conversationPersistence(
    conversation_id: Text,
) -> Generator[Conversation, None, None]:
    """Provides conversation history for a certain conversation.

    Saves any new events to the conversation storage when the context manager is exited.

    Args:
        conversation_id: The ID of the conversation. This is usually the same as the
            username.

    Returns:
        Conversation from the conversation storage.
    """
    old_conversation_events = inmemory_storage[conversation_id]
    # if old_conversation_events is None:
    #     old_conversation_events = []
    conversation = Conversation(conversation_id, old_conversation_events)

    yield conversation

class ChuckNorrisBot:
    def handle_message(self, message_text: Text, conversation: Conversation) -> None:
        conversation.addd_user_message(message_text)

        if len(conversation.conversation_events) <= 1:
            conversation.add_bot_message(f"Welcome! Let me tell you a joke.")

        joke = self.retrieve_joke()
        conversation.add_bot_message(joke)

    """
    1. retrieve_joke method can be static @staticmethod as it doesn't need access to access properties
    2. The API can be extracted to a configuration to make it more testable
    3. External API calls will always benefit from having error handlers and default 
        as they can fail unexpectedly beyond the control of this application
    """
    def retrieve_joke(self) -> Text:
        response = requests.get("https://api.chucknorris.io/jokes/random")

        return response.json()["value"]



"""
1. Inputs always needs to be validated before being used
2. Error handling needs to be in place to handle unexpected inputs and report graceful error code/message 
to the user
"""
@app.route("/user/<username>/message", methods=["POST"])
def handle_user_message(username: Text) -> Text:
    """Returns a bot response for an incoming user message.

    Args:
        username: The username which serves as unique conversation ID.

    Returns:
        The bot's responses.
    """
    message_text = request.json["text"]

    f = ChuckNorrisBot()

    with conversationPersistence(username) as conversation:
        f.handle_message(message_text, conversation)

        bot_responses = [
            x["message"] for x in conversation.new_events_dict() if x["type"] == "bot"
        ]

        return jsonify(bot_responses)


"""
1. Access to inmemory_storage[username] can be extracted to the conversation class, 
makes it easier to swap to another implementation of persistence
"""
@app.route("/user/<username>/message", methods=["GET"])
def retrieve_conversation_history(username: Text) -> Text:
    """Returns all conversation events for a user's conversation.

    Args:
        username: The username which serves as unique conversation ID.

    Returns:
        All events in this conversation, which includes user and bot messages.
    """
    history = inmemory_storage[username]
    if history:
        return jsonify(history)
    else:
        return jsonify(history), 404


if __name__ == "__main__":
    print("Serveris running")
    app.run(debug=True)