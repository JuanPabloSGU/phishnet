from utils import generate_jwt

def test_no_url_provided(client):
    data = {
        'Content-Type': 'application/json',
    }

    response = client.post("/api/v1/mlp", json=data, headers=generate_jwt(client))

    assert response.json["message"] == {"url": "URL for method is required."}


def test_invalid_url(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'blahblahblah'
    }

    response = client.post("/api/v1/mlp", json=data, headers=generate_jwt(client))

    assert response.json["message"] == "URL is invalid."


def test_not_accessible_url(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'http://blahblahblah.com'
    }

    response = client.post("/api/v1/mlp", json=data, headers=generate_jwt(client))

    assert response.json["message"] == "URL is not accessible."


def test_url_already_exists(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'https://reviewe-014035.firebaseapp.com/'
    }

    response = client.post("/api/v1/mlp", json=data, headers=generate_jwt(client))
    assert response.json["message"] == "URL already exists in Elasticsearch, returning known result."


def test_get_protocol_https(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'stackoverflow.com'
    }

    response = client.post("/api/v1/mlp", json=data, headers=generate_jwt(client))

    assert response.json["url"] == "https://stackoverflow.com/"


def test_get_protocol_http(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'example.com'
    }

    response = client.post("/api/v1/mlp", json=data, headers=generate_jwt(client))

    assert response.json["url"] == "http://example.com/"


def test_tritonMlp(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'http://example.com',
    }

    response = client.post("/api/v1/mlp", json=data, headers=generate_jwt(client))

    assert response.json["message"] == "Lexical Features extracted and stored."

def test_jwt_token(client):
    response = client.post("/api/v1/mlp")

    assert 'message' in response.json, f"Response JSON does not contain 'msg': {response.json}"

    assert response.json["message"] == "Authorization header is required."

def test_missing_bearer_word(client):
    

    headers = generate_jwt(client)
    headers['Authorization'] = headers['Authorization'].split()[1:]
    
    response = client.post("/api/v1/mlp", headers=headers)

    assert response.json['message'] == 'Authorization header must start with Bearer.'

def test_missing_token(client):

  headers = generate_jwt(client)
  headers['Authorization'] = headers['Authorization'].split()[0]

  response = client.post("/api/v1/mlp", headers=headers)

  assert response.json['message'] == 'Token must be present with Bearer.'

def test_jwt_token_validation(client):
    headers = {
        'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjI4ODgyODE0OTE0NjM4NTkzOSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3ppdGFkZWwuZGF0YWJlbmRpbmcuY2EiLCJzdWIiOiIyNzkyNjY2NzI2Njg5NjMxODYiLCJhdWQiOlsiMjg3MjcyNTExOTkxODQwMjc1IiwiMjg4Mjk2MzI2MDQ1NzYxMDQzIiwiMjg3MjcyMzUzMjk2MDg4NTk1Il0sImV4cCI6MTcyODY5NTcwNiwiaWF0IjoxNzI4NjUyNTA2LCJhdXRoX3RpbWUiOjE3MjgzMzM2NDIsIm5vbmNlIjoid3V1OThzazUwdmoiLCJhbXIiOlsicHdkIl0sImF6cCI6IjI4NzI3MjUxMTk5MTg0MDI3NSIsImNsaWVudF9pZCI6IjI4NzI3MjUxMTk5MTg0MDI3NSIsImF0X2hhc2giOiJyOFN0TFpsNzFFbXEzQW1OQmJCR0F3Iiwic2lkIjoiVjFfMjg2ODAwMDU3MjAwNjA2NzM5IiwibmFtZSI6IkFkYW0gSmFzbmlld2ljeiIsImdpdmVuX25hbWUiOiJBZGFtIiwiZmFtaWx5X25hbWUiOiJKYXNuaWV3aWN6Iiwibmlja25hbWUiOiJBZGFtIiwiZ2VuZGVyIjoibWFsZSIsImxvY2FsZSI6ImVuIiwidXBkYXRlZF9hdCI6MTcyMjk1Mjc0NCwicHJlZmVycmVkX3VzZXJuYW1lIjoiYWRhbUBkYXRhYmVuZGluZy5jYSIsImVtYWlsIjoiYWRhbUBkYXRhYmVuZGluZy5jYSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlfQ.ZwA0LL-NmG-XBmYhiufRdBgskgOCP6a36fMkN4N-bvo5RaqX2nPNb-DNaHoREcmtt7LIy22CFO972M36DYnEz0azP2dHd7RnF4s7M4ibilnuGxk3YBlgd3cu7LutnSk4BfPP1PBpX3A959fq6ZWA6Sjf942wyXD_HBV9NKY9ufZ74TjaJW6ipifZK-irkcZ3-X0HaG0P33ibssvwLRb_xvyzltPKhBe9WL7BGEdzKun7vpxIN4OaIJV0cp56KuZtGihCJLcvu6HpM_8aQdubS_bA48xOlBu5jnw6B9XNiJq3ByEc78mJyJtTD3DY5bhFT4Od6r6JK5S4GbNKq6fJgw'
    }
    response = client.post("/api/v1/mlp", headers=headers)

    assert response.json["message"] == "Invalid token."