def generate_jwt(client):
    data = {
        'Content-Type': 'application/json',
        'username': 'test',
        'password': 'password'
    }

    response = client.post("/api/v1/login", json=data)
    access_token = response.json["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    return headers
