import stripe
import os
from django.shortcuts import render, redirect
from django.http import JsonResponse

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')

def create_checkout_session(request):
    try:
        total_amount = 5000
        platform_fee = int(total_amount * 0.1)

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'jpy',
                    'product_data': {
                        'name': 'ご飲食代（El\'christo決済）',
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
            success_url='http://localhost:8000/success/',
            cancel_url='http://localhost:8000/cancel/',
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def success(request):
    return render(request, 'account/success.html')

def cancel(request):
    return render(request, 'account/cancel.html')