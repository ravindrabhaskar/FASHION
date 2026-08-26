from django.urls import path

from orders import views

urlpatterns = [
    path("", views.OrderListView.as_view(), name="orders"),
    path("<uuid:order_id>", views.OrderDetailView.as_view(), name="order-detail"),
    path("<uuid:order_id>/transition", views.OrderTransitionView.as_view(),
         name="order-transition"),
]
