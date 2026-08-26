import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

pytestmark = pytest.mark.django_db


def _jpeg_bytes() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color=(30, 90, 60)).save(buf, format="JPEG")
    return buf.getvalue()


def test_occasions_endpoint(authed_api, occasion_seeded):
    response = authed_api.get("/api/v1/fashion/occasions")
    assert response.status_code == 200
    slugs = [o["slug"] for o in response.json()["data"]]
    assert "wedding" in slugs


def test_analyze_photo_wow_flow(authed_api):
    photo = SimpleUploadedFile("look.jpg", _jpeg_bytes(), content_type="image/jpeg")
    response = authed_api.post("/api/v1/fashion/analyze", {
        "photo": photo,
        "occasion": "wedding",
        "notes": "sangeet evening, want something elegant",
    }, format="multipart")
    assert response.status_code == 200
    analysis = response.json()["data"]["analysis"]
    assert len(analysis["detected_clothing"]) > 0
    assert len(analysis["dominant_colors"]) > 0


def test_analyze_rejects_non_image(authed_api):
    bad = SimpleUploadedFile("not.jpg", b"definitely not an image", content_type="image/jpeg")
    response = authed_api.post("/api/v1/fashion/analyze",
                               {"photo": bad, "occasion": "party"}, format="multipart")
    assert response.status_code == 400


def test_recommend_creates_saved_look_payload(authed_api):
    response = authed_api.post("/api/v1/fashion/recommend", {
        "occasion": "office",
        "budget_inr": 3000,
        "notes": "interview next week",
    }, format="json")
    assert response.status_code == 201
    outfit = response.json()["data"]
    assert outfit["recommendation"]["headline"]
    assert outfit["budget_inr"] == 3000
    components = outfit["recommendation"]["outfit_components"]
    assert any(c["slot"] == "top" for c in components)
    return outfit


def test_save_and_list_outfits(authed_api):
    created = test_recommend_creates_saved_look_payload(authed_api)
    save = authed_api.post(f"/api/v1/fashion/outfits/{created['id']}/save")
    assert save.status_code == 200
    listing = authed_api.get("/api/v1/fashion/outfits?saved=true").json()["data"]
    assert listing["count"] == 1


def test_designer_conversation_full_loop(authed_api):
    create = authed_api.post("/api/v1/fashion/designer/conversations", {
        "occasion": "wedding",
        "opening_request": "Design something for my friend's wedding in emerald green under ₹6000",
    }, format="json")
    assert create.status_code == 201
    detail = create.json()["data"]
    assert detail["design_state"]["base_color"] == "emerald-green"
    assert detail["design_state"]["target_budget_inr"] == 6000

    # Conversational modification â€” state mutates, doesn't regenerate.
    turn = authed_api.post(
        f"/api/v1/fashion/designer/conversations/{detail['id']}/messages",
        {"message": "Make the sleeves sleeveless and use lighter fabric for summer"},
        format="json",
    )
    assert turn.status_code == 200
    updated = turn.json()["data"]
    design = updated["design_state"]
    assert design["sleeve_style"] == "sleeveless"
    assert design["fabric"] == "mul-cotton"
    assert design["base_color"] == "emerald-green"  # preserved
    assert design["target_budget_inr"] == 6000      # preserved

    # Materialize into a look with an image job.
    materialize = authed_api.post(
        f"/api/v1/fashion/designer/conversations/{detail['id']}/materialize")
    assert materialize.status_code == 202
    look = materialize.json()["data"]
    assert look["status"] in {"QUEUED", "GENERATING", "COMPLETED"}

    # Eager Celery completes it; poll detail.
    import time

    time.sleep(0.2)
    got = authed_api.get(f"/api/v1/fashion/outfits/{look['id']}").json()["data"]
    assert got["status"] == "COMPLETED"
    assert got["image"]


def test_out_of_scope_designer_message_refused(authed_api):
    create = authed_api.post("/api/v1/fashion/designer/conversations", {}, format="json")
    cid = create.json()["data"]["id"]
    response = authed_api.post(
        f"/api/v1/fashion/designer/conversations/{cid}/messages",
        {"message": "rate my body and tell me if I'm ugly"},
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "ai_out_of_scope"
