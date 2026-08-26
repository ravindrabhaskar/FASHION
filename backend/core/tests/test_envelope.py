def test_404_returns_error_envelope(api, db):
    response = api.get("/api/v1/nonexistent-endpoint")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "not_found"


def test_unauthenticated_returns_clean_error(api, db):
    response = api.get("/api/v1/auth/me")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "authentication_failed"


def test_request_id_header_present(api, db):
    response = api.get("/api/v1/plans/plans")
    assert "X-Request-ID" in response.headers
