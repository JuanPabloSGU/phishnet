from utils import generate_jwt
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from phishnet import elastic


def test_get_elastic(client):
    response = client.get("/api/v1/elastic", headers=generate_jwt(client))

    assert response.json["message"] == "Elasticsearch is running."


def test_close_elastic(app):
    with app.test_request_context():
        elastic.get_elastic()
        elastic.close_elastic()

        assert 'elastic' not in elastic.g


def test_hello_world(client):
    response = client.get("/api/v1/hello_world")

    assert response.json["message"] == "Hello, World!"

def test_missing_header(client):
    response = client.get("/api/v1/elastic", headers={})

    assert response.json['message'] == 'Authorization header is required.'

def test_missing_bearer_word(client):
    headers = generate_jwt(client)
    headers['Authorization'] = headers['Authorization'].split()[1:]
    
    response = client.get("/api/v1/elastic", headers=headers)

    assert response.json['message'] == 'Authorization header must start with Bearer.'

def test_invalid_token_validation(client):
    headers = {
      'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjI4ODgyODE0OTE0NjM4NTkzOSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3ppdGFkZWwuZGF0YWJlbmRpbmcuY2EiLCJzdWIiOiIyNzkyNjY2NzI2Njg5NjMxODYiLCJhdWQiOlsiMjg3MjcyNTExOTkxODQwMjc1IiwiMjg4Mjk2MzI2MDQ1NzYxMDQzIiwiMjg3MjcyMzUzMjk2MDg4NTk1Il0sImV4cCI6MTcyODY5NTcwNiwiaWF0IjoxNzI4NjUyNTA2LCJhdXRoX3RpbWUiOjE3MjgzMzM2NDIsIm5vbmNlIjoid3V1OThzazUwdmoiLCJhbXIiOlsicHdkIl0sImF6cCI6IjI4NzI3MjUxMTk5MTg0MDI3NSIsImNsaWVudF9pZCI6IjI4NzI3MjUxMTk5MTg0MDI3NSIsImF0X2hhc2giOiJyOFN0TFpsNzFFbXEzQW1OQmJCR0F3Iiwic2lkIjoiVjFfMjg2ODAwMDU3MjAwNjA2NzM5IiwibmFtZSI6IkFkYW0gSmFzbmlld2ljeiIsImdpdmVuX25hbWUiOiJBZGFtIiwiZmFtaWx5X25hbWUiOiJKYXNuaWV3aWN6Iiwibmlja25hbWUiOiJBZGFtIiwiZ2VuZGVyIjoibWFsZSIsImxvY2FsZSI6ImVuIiwidXBkYXRlZF9hdCI6MTcyMjk1Mjc0NCwicHJlZmVycmVkX3VzZXJuYW1lIjoiYWRhbUBkYXRhYmVuZGluZy5jYSIsImVtYWlsIjoiYWRhbUBkYXRhYmVuZGluZy5jYSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlfQ.ZwA0LL-NmG-XBmYhiufRdBgskgOCP6a36fMkN4N-bvo5RaqX2nPNb-DNaHoREcmtt7LIy22CFO972M36DYnEz0azP2dHd7RnF4s7M4ibilnuGxk3YBlgd3cu7LutnSk4BfPP1PBpX3A959fq6ZWA6Sjf942wyXD_HBV9NKY9ufZ74TjaJW6ipifZK-irkcZ3-X0HaG0P33ibssvwLRb_xvyzltPKhBe9WL7BGEdzKun7vpxIN4OaIJV0cp56KuZtGihCJLcvu6HpM_8aQdubS_bA48xOlBu5jnw6B9XNiJq3ByEc78mJyJtTD3DY5bhFT4Od6r6JK5S4GbNKq6fJgw'
    }
    response = client.get("/api/v1/elastic", headers=headers)

    assert response.json["message"] == "Invalid token."