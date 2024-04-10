def test_no_token(client):
    response = client.get("/api/v1/elastic")

    assert response.json["msg"] == "Missing Authorization Header"
