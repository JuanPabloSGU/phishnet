from utils import generate_jwt

def test_no_url_provided(client):
    data = {
        'Content-Type': 'application/json',
    }

    response = client.post("/api/v1/urlBert", json=data, headers=generate_jwt(client))

    assert response.json["message"] == {"url": "URL for method is required."}

def test_invalid_url(client):
    data = {
        'Content-Type': 'application/json',
        'url': ''
    }

    response = client.post("/api/v1/urlBert", json=data, headers=generate_jwt(client))

    assert response.json["message"] == "URL is invalid."

def test_not_accessible_url(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'http://blahblahblah.com'
    }

    response = client.post("/api/v1/urlBert", json=data, headers=generate_jwt(client))

    assert response.json["message"] == "URL is not accessible."

def test_url_already_exists(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'https://reviewe-014035.firebaseapp.com/'
    }

    response = client.post("/api/v1/urlBert", json=data, headers=generate_jwt(client))
    assert response.json["message"] == "URL already exists in Elasticsearch."

def test_triton_urlBert(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'http://www.google.com',
    }

    response = client.post("/api/v1/urlBert", json=data, headers=generate_jwt(client))

    assert response.json["message"] == "Url Inference complete."