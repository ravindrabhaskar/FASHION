"""Phase 7 tests: trends, multilingual/i18n, translate, virtual try-on."""
import pytest

pytestmark = pytest.mark.django_db


def _seed_product(api, user):
    from designers.models import DesignerProfile

    DesignerProfile.objects.create(
        user=user, slug="trend-studio", studio_name="Trend Studio", city="Jaipur"
    )
    response = api.post("/api/v1/marketplace/products", {
        "title": "Bandhani wrap",
        "category": "ethnic",
        "price_inr": 1999,
        "stock": 5,
        "fabric": "silk",
        "colors": ["magenta", "navy"],
        "city": "Jaipur",
    }, format="json")
    assert response.status_code == 201
    return response.json()["data"]


def test_trends_snapshot_reflects_catalog_and_posts(authed_api, user):
    import io

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    _seed_product(authed_api, user)
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color=(200, 40, 60)).save(buf, format="JPEG")
    photo = SimpleUploadedFile("post.jpg", buf.getvalue(), content_type="image/jpeg")
    authed_api.post("/api/v1/social/posts", {
        "caption": "Rocking my new look #silk #jaipur #weddingwear",
        "occasion": "wedding",
        "photo": photo,
    }, format="multipart")

    trends = authed_api.get("/api/v1/fashion/trends").json()["data"]
    assert trends["generated_at"]
    assert {"value": "magenta", "count": 1, "label": "magenta"} in trends["colors"]
    assert any(t["value"] == "silk" for t in trends["fabrics"])
    assert any(t["value"] == "ethnic" for t in trends["categories"])
    hashtag_values = {t["value"] for t in trends["hashtags"]}
    assert "silk" in hashtag_values and "jaipur" in hashtag_values


def test_trends_empty_db_still_returns_sections(authed_api):
    trends = authed_api.get("/api/v1/fashion/trends").json()["data"]
    assert trends["colors"] == []
    assert {"colors", "fabrics", "categories", "hashtags", "cities"} <= set(trends)


def test_i18n_strings_localized_with_en_fallback(authed_api):
    data = authed_api.get("/api/v1/fashion/i18n/strings?lang=hi").json()["data"]
    assert data["locale"] == "hi"
    assert data["strings"]["auth.sign_in"] == "साइन इन करें"
    # English is always present as fallback; every key resolves for any locale.
    bn = authed_api.get("/api/v1/fashion/i18n/strings?lang=bn").json()["data"]["strings"]
    assert bn["nav.profile"] == "প্রোফাইল"
    unknown = authed_api.get("/api/v1/fashion/i18n/strings?lang=xx").json()["data"]["strings"]
    assert unknown["action.save"] == "Save"


def test_translate_known_string_and_pass_through(authed_api):
    known = authed_api.post("/api/v1/ai/translate",
                            {"text": "Save", "target": "hi"}, format="json").json()["data"]
    assert known["mode"] == "dict"
    assert known["text"] == "सहेजें"

    free = authed_api.post("/api/v1/ai/translate",
                           {"text": "A custom khadi overcoat.", "target": "te"},
                           format="json").json()["data"]
    assert free["mode"] == "pass-through"
    assert free["text"] == "A custom khadi overcoat."
    assert free["target"] == "te"


def test_translate_requires_text(authed_api):
    response = authed_api.post("/api/v1/ai/translate", {"target": "hi"}, format="json")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "text_required"


def test_virtual_tryon_creates_queued_outfit(authed_api, user):
    from fashion.models import GeneratedOutfit

    base = GeneratedOutfit.objects.create(
        user=user,
        source=GeneratedOutfit.Source.STYLIST,
        status=GeneratedOutfit.Status.COMPLETED,
        title="Emerald anarkali",
        occasion="wedding",
        recommendation={
            "headline": "Emerald anarkali",
            "outfit_components": [
                {"slot": "dress", "item": {"description": "emerald anarkali with gold zari"}}
            ],
        },
    )
    response = authed_api.post("/api/v1/fashion/outfits/{}/tryon".format(base.id),
                               format="json")
    assert response.status_code == 202
    data = response.json()["data"]
    assert data["source"] == "CUSTOMIZE"
    assert data["status"] in ("QUEUED", "GENERATING", "COMPLETED")
    assert 'Try-on' in data["title"]
    assert data["image"]  # eager celery mock provider renders instantly