from django.urls import path

from payments import views

urlpatterns = [
    path("pay", views.PayView.as_view(), name="pay"),
    path("<uuid:payment_id>/confirm", views.ConfirmView.as_view(), name="pay-confirm"),
    path("webhook/<str:provider>", views.WebhookView.as_view(), name="pay-webhook"),
]
