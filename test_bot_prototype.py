import pytest
from flask.testing import FlaskClient

import bot_prototype


@pytest.fixture
def client() -> FlaskClient:
    """Returns a client which can be used to test the HTTP API."""
    bot_prototype.app.config["TESTING"] = True

    with bot_prototype.app.test_client() as client:
        yield client


def test_send_message(client: FlaskClient):
    response = client.post("/user/test/message", json={"text": "Hello"})

    assert response.status_code == 200
    response_body = response.json


def test_retrieve_history(client: FlaskClient):
    client.post("/user/test_retrieve/message", json={"text": "Hello"})

    response = client.get("/user/test_retrieve/message")
    assert response.status_code == 200
    history = response.json

    assert len(history) == 3

    assert history[0] == {"message": "Hello", "type": "user"}
    assert history[1] == {"message": "Welcome! Let me tell you a joke.", "type": "bot"}
    assert history[2]["type"] == "bot"


def test_retrieve_history_after_multiple_post_should_return_only_one_joke(client: FlaskClient):
    first_post_reponse = client.post("/user/test_multiple/message", json={"text": "Hello"})

    assert first_post_reponse.status_code == 200

    second_post_reponse = client.post("/user/test_multiple/message", json={"text": "World!!"})

    assert second_post_reponse.status_code == 200

    response = client.get("/user/test_multiple/message")
    assert response.status_code == 200
    history = response.json

    assert len(history) == 5

    bot_responses = [
        x["message"] for x in history if x["type"] == "bot"
    ]

    assert len(bot_responses) == 3


def test_bot_should_persist_multiple_user_messages(client: FlaskClient):
    user1_post_response = client.post("/user/user1/message", json={"text": "Hello"})

    assert user1_post_response.status_code == 200

    user2_post_response = client.post("/user/user2/message", json={"text": "World!!"})

    assert user2_post_response.status_code == 200

    user1_history = client.get("/user/user1/message").json
    assert len(user1_history) == 3

    user2_history = client.get("/user/user2/message").json
    assert len(user2_history) == 3


def test_bot_should_return_error_for_non_json_input(client: FlaskClient):
    with pytest.raises(TypeError) as execinfo:
        client.post("/user/user1/message", data="Hello")
    assert str(execinfo.value) == "'NoneType' object is not subscriptable"

