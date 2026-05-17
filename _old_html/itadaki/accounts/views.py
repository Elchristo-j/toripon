import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse

# 本来は settings.py に書くべきですが、まずは動作確認のためにここに記述します
stripe.api_key = "sk_test_51R4urxDFW7Advb6A9kIfERDeeRTlKgp2eWwOiZdriRj58lG5qViZdQABdLbH3nzTYnWLuMTFwYKXeoXl6AS55NKp00y2x8nCRl"

def create_checkout_session(request):
    """
    お客さんの注文合計を受け取り、Stripeの決済画面へリダイレクトするビュー
    """
    try:
        # 本番ではフロントエンドやデータベースから合計金額を取得します
        total_amount = 5000  # 例：5,000円
        
        # El'christoの取り分（プラットフォーム手数料）の計算
        # 例：売上の10%をいただく場合
        platform_fee = int(total_amount * 0.1) 

        # Stripe Checkout セッションの作成
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

            # --- ここがSaaS（Connect）の重要設定 ---
            payment_intent_data={
                # あなた（親）に自動転送される金額
                'application_fee_amount': platform_fee,
            },
            # 決済を行う店舗（子）のID
            stripe_account="acct_1TX79HRWBqIOfYb3",
            # ------------------------------------

            # 決済成功・キャンセル後の戻り先（URLはご自身の環境に合わせて調整してください）
            success_url='http://localhost:8000/success/',
            cancel_url='http://localhost:8000/cancel/',
        )

        # Stripeの決済ページへリダイレクト
        return redirect(session.url, code=303)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def success(request):
    return render(request, 'account/success.html')

def cancel(request):
    return render(request, 'account/cancel.html')