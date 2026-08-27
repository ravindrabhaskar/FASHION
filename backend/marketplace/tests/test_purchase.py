"""Tests for catalog product management + direct purchase (buy now)."""
import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _make_seller(api, user):
    from designers.models import DesignerProfile

    DesignerProfile.objects.create(
        user=user, slug="test-studio", studio_name="Test Studio", city="Jaipur"
    )
    response = api.post("/api/v1/marketplace/products", {
        "title": "Handloom saree",
        "description": "Madder-dyed cotton saree",
        "category": "ethnic",
        "price_inr": 4999,
        "stock": 3,
        "city": "Jaipur",
        "fabric": "cotton",
    }, format="json")
    assert response.status_code == 201
    return response.json()["data"]


def _login_as(api, email, password):
    response = api.post("/api/v1/auth/login", {"email": email, "password": password},
                        format="json")
    token = response.json()["data"]["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api


def test_create_product_requires_seller(authed_api):
    response = authed_api.post("/api/v1/marketplace/products", {
        "title": "No-seller kurta", "price_inr": 500, "stock": 1,
    }, format="json")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "seller_required"


def test_catalog_purchase_creates_created_order(authed_api, user):
    product = _make_seller(authed_api, user)
    res = authed_api.post(f"/api/v1/marketplace/products/{product['id']}/buy",
                          {"quantity": 2}, format="json")
    assert res.status_code == 201
    order = res.json()["data"]
    assert order["status"] == "CREATED"
    assert order["amount_inr"] == 4999 * 2
    assert order["quantity"] == 2
    assert order["seller_user_id"] == str(user.id)
    assert order["title"] == "Handloom saree"
    assert order["seller_name"] == user.full_name


def test_catalog_purchase_insufficient_stock(authed_api, user):
    product = _make_seller(authed_api, user)
    from marketplace.models import Product

    Product.objects.filter(id=product["id"]).update(stock=1)
    res = authed_api.post(f"/api/v1/marketplace/products/{product['id']}/buy",
                          {"quantity": 5}, format="json")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "insufficient_stock"


def test_catalog_purchase_isolated_between_users(authed_api, user):
    from django.contrib.auth import get_user_model

    seller_email = user.email
    seller_password = "strong-pass-1"
    product = _make_seller(authed_api, user)

    buyer = get_user_model().objects.create_user(email="buyer@example.com",
                                                 password="buyer-pass-1", full_name="Buyer One")
    buyer_api = _login_as(APIClient(), buyer.email, "buyer-pass-1")
    res = buyer_api.post(f"/api/v1/marketplace/products/{product['id']}/buy",
                         {"quantity": 1}, format="json")
    assert res.status_code == 201
    order = res.json()["data"]
    assert order["customer_name"] == "Buyer One"
    assert order["seller_user_id"] == str(user.id)
    assert seller_email  # keep reference
    assert seller_password


def test_product_patch_updates_fields(authed_api, user):
    product = _make_seller(authed_api, user)
    patched = authed_api.patch(f"/api/v1/marketplace/products/{product['id']}",
                               {"title": "Upcycled saree", "price_inr": 5500}, format="json")
    assert patched.status_code == 200
    data = patched.json()["data"]
    assert data["title"] == "Upcycled saree"
    assert data["price_inr"] == 5500


def test_product_patch_replaces_photo(authed_api, user):
    import io

    from PIL import Image

    from django.core.files.uploadedfile import SimpleUploadedFile

    product = _make_seller(authed_api, user)
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color=(20, 40, 90)).save(buf, format="PNG")
    photo = SimpleUploadedFile("new.png", buf.getvalue(), content_type="image/png")
    patched = authed_api.patch(f"/api/v1/marketplace/products/{product['id']}",
                               {"photo": photo}, format="multipart")
    assert patched.status_code == 200
    data = patched.json()["data"]
    assert data["image"]
    assert "products/" in data["image"]