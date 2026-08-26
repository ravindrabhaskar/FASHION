import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

pytestmark = pytest.mark.django_db


def _jpeg_bytes(color=(30, 90, 60)) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color=color).save(buf, format="JPEG")
    return buf.getvalue()


def _add_item(api, name="My kurta set", category="", notes="") -> dict:
    photo = SimpleUploadedFile("piece.jpg", _jpeg_bytes(), content_type="image/jpeg")
    payload = {"photo": photo}
    if category:
        payload["category"] = category
    if notes:
        payload["notes"] = notes
    response = api.post("/api/v1/wardrobe/items", payload, format="multipart")
    assert response.status_code == 201
    item = response.json()["data"]
    assert item["status"] == "READY"  # mock extraction completes synchronously
    assert item["name"] == name or item["name"]
    return item


def test_add_item_extracts_attributes(authed_api):
    item = _add_item(authed_api, notes="printed cotton shirt")
    # Mock vision analysis always yields colors + clothing + occasions.
    assert item["color_primary"]
    assert item["formality"] in (1, 2, 3, 4, 5)
    assert isinstance(item["occasion_slugs"], list)


def test_list_filter_category_and_favorite(authed_api):
    _add_item(authed_api)
    listing = authed_api.get("/api/v1/wardrobe/items").json()["data"]
    assert listing["count"] >= 1

    authed_api.patch(f"/api/v1/wardrobe/items/{listing['results'][0]['id']}",
                     {"favorite": True}, format="json")
    favs = authed_api.get("/api/v1/wardrobe/items?favorite=true").json()["data"]
    assert favs["count"] == 1

    missing = authed_api.get("/api/v1/wardrobe/items?category=bogus")
    assert missing.status_code == 400


def test_patch_and_delete_item(authed_api):
    item = _add_item(authed_api)
    patched = authed_api.patch(f"/api/v1/wardrobe/items/{item['id']}", {
        "name": "Emerald kurta",
        "category": "ethnic",
        "notes": "for sangeet",
    }, format="json")
    assert patched.status_code == 200
    data = patched.json()["data"]
    assert data["name"] == "Emerald kurta"
    assert data["category"] == "ethnic"
    assert data["category_label"]

    deleted = authed_api.delete(f"/api/v1/wardrobe/items/{item['id']}")
    assert deleted.status_code == 204
    gone = authed_api.get(f"/api/v1/wardrobe/items/{item['id']}")
    assert gone.status_code == 404


def test_mark_worn_increments_counter(authed_api):
    item = _add_item(authed_api)
    first = authed_api.post(f"/api/v1/wardrobe/items/{item['id']}/worn").json()["data"]
    second = authed_api.post(f"/api/v1/wardrobe/items/{item['id']}/worn").json()["data"]
    assert second["times_worn"] == first["times_worn"] + 1
    assert second["last_worn_at"]


def test_closet_recommend_requires_items(authed_api):
    response = authed_api.post("/api/v1/wardrobe/closet/recommend",
                               {"occasion": "casual"}, format="json")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "wardrobe_too_small"


def test_closet_recommend_full_flow(authed_api):
    _add_item(authed_api)  # top-ish per mock extraction
    _add_item(authed_api)
    _add_item(authed_api)

    response = authed_api.post("/api/v1/wardrobe/closet/recommend", {
        "occasion": "office",
    }, format="json")
    assert response.status_code == 201
    data = response.json()["data"]

    outfit = data["outfit"]
    assert outfit["source"] == "WARDROBE"
    assert outfit["recommendation"]["headline"]
    used_ids = outfit["design_state"]["wardrobe_item_ids"]
    assert len(used_ids) >= 1
    returned_ids = {i["id"] for i in data["items"]}
    assert set(used_ids) <= returned_ids

    # The look is saveable through the normal saved-looks flow.
    save = authed_api.post(f"/api/v1/fashion/outfits/{outfit['id']}/save")
    assert save.status_code == 200


def test_daily_suggestion_payload(authed_api, user):
    profile = user.profile
    profile.city = "Mumbai"
    profile.save(update_fields=["city"])

    response = authed_api.get("/api/v1/wardrobe/daily")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["occasion"]
    assert data["headline"]
    assert data["weather"]["temp_c"]  # seasonal fallback works with zero network
    assert isinstance(data["tips"], list) and data["tips"]
    # Fewer than 2 items → no closet pick yet.
    assert data["closet_outfit"] is None


def test_daily_suggestion_includes_closet_pick(authed_api):
    _add_item(authed_api)
    _add_item(authed_api)
    data = authed_api.get("/api/v1/wardrobe/daily?city=Hyderabad").json()["data"]
    assert data["closet_outfit"] is not None
    rec = data["closet_outfit"]["recommendation"]
    assert rec["headline"]
    assert rec["used_item_ids"]
    for brief in data["closet_outfit"]["items"]:
        assert brief["image"]  # views fill absolute image URLs


def test_wardrobe_quota_enforced_for_free_tier(api, authed_api, settings):
    from unittest import mock

    from subscriptions.services import FREE_ENTITLEMENTS

    limit = FREE_ENTITLEMENTS["wardrobe_item_limit"]
    with mock.patch("subscriptions.services.get_entitlements") as mocked:
        ent = mocked.return_value
        ent.wardrobe_item_limit = limit
        # Simulate a full wardrobe by making count query return the limit via DB loop:
        # simpler — patch WardrobeItem count indirectly by lowering limit to current usage.
        created = _add_item(authed_api)
        ent.wardrobe_item_limit = 1  # now full
        response = api.post("/api/v1/wardrobe/items", {
            "photo": SimpleUploadedFile("x.jpg", _jpeg_bytes(), content_type="image/jpeg"),
        }, format="multipart")
        assert response.status_code == 429 or response.status_code == 400
        body = response.json()
        assert body["error"]["code"] == "quota_exceeded"
        assert created  # keeps fixture referenced


def test_item_isolation_between_users(api, authed_api, user):
    from django.contrib.auth import get_user_model

    item = _add_item(authed_api)

    other = get_user_model().objects.create_user(email="other@example.com",
                                                 password="strong-pass-2", full_name="Other")
    response = api.post("/api/v1/auth/login", {"email": other.email, "password": "strong-pass-2"},
                        format="json")
    token = response.json()["data"]["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    listing = api.get("/api/v1/wardrobe/items").json()["data"]
    assert listing["count"] == 0
    detail = api.get(f"/api/v1/wardrobe/items/{item['id']}")
    assert detail.status_code == 404


def test_rejects_non_image_upload(authed_api):
    bad = SimpleUploadedFile("not.jpg", b"definitely not an image", content_type="image/jpeg")
    response = authed_api.post("/api/v1/wardrobe/items", {"photo": bad}, format="multipart")
    assert response.status_code == 400
