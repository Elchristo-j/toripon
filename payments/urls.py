from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # BUG FIX: Stripe Webhook エンドポイント（以前は存在しなかった）
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
