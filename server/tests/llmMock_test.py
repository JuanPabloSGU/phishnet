from utils import generate_jwt

def test_no_url_provided(client):
    data = {
        'Content-Type': 'application/json',
    }

    response = client.post("/api/v1/llm_mock", json=data, headers=generate_jwt(client))

    assert response.json["message"] == {"url": "URL for method is required."}

def test_invalid_url(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'invalid_url'
    }

    response = client.post("/api/v1/llm_mock", json=data, headers=generate_jwt(client))

    assert response.json["message"] == "URL is invalid."


def test_successful_llm_mock(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'http://example.com'
    }

    response = client.post("/api/v1/llm_mock", json=data, headers=generate_jwt(client))

    assert response.status_code == 200
    assert 'message' in response.json

def test_jwt_token(client):
    response = client.post("/api/v1/llm_mock")

    assert 'message' in response.json, f"Response JSON does not contain 'msg': {response.json}"

    assert response.json["message"] == "Authorization header is required."

def test_missing_bearer_word(client):
    

    headers = generate_jwt(client)
    headers['Authorization'] = headers['Authorization'].split()[1:]
    
    response = client.post("/api/v1/llm_mock", headers=headers)

    assert response.json['message'] == 'Authorization header must start with Bearer.'

def test_missing_token(client):

  headers = generate_jwt(client)
  headers['Authorization'] = headers['Authorization'].split()[0]

  response = client.post("/api/v1/llm_mock", headers=headers)

  assert response.json['message'] == 'Token must be present with Bearer.'