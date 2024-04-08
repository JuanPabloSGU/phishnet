from utils import generate_jwt


def test_triton_mlp(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'http://example.com',
    }

    response = client.post("/api/v1/mlp", json=data, headers=generate_jwt(client))

    assert response.json["message"] == "Lexical Features extracted and stored."
