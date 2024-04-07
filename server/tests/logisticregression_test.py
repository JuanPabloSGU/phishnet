def test_no_url_provided(client):
    data = {
        'Content-Type': 'application/json',
    }
    response = client.post("/api/v1/logres", json=data)

    assert response.json["message"] == {"url": "URL for method is required."}


def test_invalid_url(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'blahblahblah'
    }
    response = client.post("/api/v1/logres", json=data)
    assert response.json["message"] == "URL is invalid."


def test_not_accessible_url(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'http://blahblahblah.com'
    }

    response = client.post("/api/v1/logres", json=data)

    assert response.json["message"] == "URL is not accessible."


def test_url_already_exists(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'http://ftyvf.blogspot.li/'
    }

    response = client.post("/api/v1/logres", json=data)

    assert response.json["message"] == "URL already exists in Elasticsearch."


def test_get_protocol_https(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'stackoverflow.com'
    }

    response = client.post("/api/v1/logres", json=data)

    assert response.json["url"] == "https://stackoverflow.com/"


def test_get_protocol_http(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'example.com'
    }

    response = client.post("/api/v1/logres", json=data)

    assert response.json["url"] == "http://example.com/"


def test_triton_logisticregression(client):
    data = {
        'Content-Type': 'application/json',
        'url': 'http://example.com',
    }

    response = client.post("/api/v1/logres", json=data)

    assert response.json["message"] == "Lexical Features extracted and stored."
