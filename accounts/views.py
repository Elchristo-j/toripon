import stripe
import os
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')


def _base_url(request):
    """本番・開発どちらでも正しいベースURLを返す"""
    if hasattr(settings, 'SITE_URL') and settings.SITE_URL:
        return settings.SITE_URL.rstrip('/')
    return request.build_absolute_uri('/').rstrip('/')


def create_checkout_session(request):
    try:
        total_amount = 5000
        platform_fee = int(total_amount * 0.1)

        base = _base_url(request)

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'jpy',
                    'product_data': {
                        'name': "ご飲食代（El'christo決済）",
                    },
                    'unit_amount': total_amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            payment_intent_data={
                'application_fee_amount': platform_fee,
            },
            stripe_account=os.environ.get('STRIPE_CONNECT_ACCOUNT_ID', ''),
            # BUG FIX: localhost 固定をやめ、実際のリクエストURLから生成する
            success_url=f'{base}/accounts/success/',
            cancel_url=f'{base}/accounts/cancel/',
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def success(request):
    # BUG FIX: 'account/success.html' → 'accounts/success.html'（アプリ名は複数形）
    return render(request, 'accounts/success.html')


def cancel(request):
    # BUG FIX: 'account/cancel.html' → 'accounts/cancel.html'（アプリ名は複数形）
    return render(request, 'accounts/cancel.html')
