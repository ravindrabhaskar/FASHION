from django.urls import path

from marketplace import views

urlpatterns = [
    path("products", views.ProductsView.as_view(), name="products"),
    path("products/<uuid:product_id>", views.ProductDetailView.as_view(), name="product-detail"),
    path("search", views.SearchView.as_view(), name="marketplace-search"),
    path("posts/<uuid:post_id>/shop", views.ShopThisLookView.as_view(), name="shop-this-look"),
    path("quotes", views.QuoteRequestView.as_view(), name="quotes"),
    path("quotes/<uuid:request_id>/offers", views.QuoteOfferView.as_view(), name="quote-offers"),
    path("offers/<uuid:offer_id>/accept", views.QuoteAcceptView.as_view(), name="quote-accept"),
    path("products/<uuid:product_id>/buy", views.CatalogPurchaseView.as_view(), name="product-buy"),
]
