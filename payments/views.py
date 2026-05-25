"""
payments/views.py
Stripe Webhook ハンドラー

BUG FIX: 以前は空ファイルだったため Webhook イベントを一切処理できなかった。
対応イベント:
  - checkout.session.completed   → 注文を決済済みにマーク
  - payment_intent.payment_failed → 失敗ログ記録（将来の通知拡張用）
"""

import json
import os
import stripe
import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    # ── 署名検証 ──────────────────────────────────────────────────
    if WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
        except stripe.error.SignatureVerificationError:
            logger.warning('Stripe Webhook: 署名検証失敗')
            return HttpResponse(status=400)
        except Exception as e:
            logger.error(f'Stripe Webhook: 予期しないエラー {e}')
            return HttpResponse(status=400)
    else:
        # 開発環境: 署名なしで解析（本番では STRIPE_WEBHOOK_SECRET を必ず設定すること）
        try:
            event = stripe.Event.construct_from(
                json.loads(payload), stripe.api_key
            )
        except Exception as e:
            logger.error(f'Stripe Webhook: ペイロード解析エラー {e}')
            return HttpResponse(status=400)

    # ── イベント処理 ───────────────────────────────────────────────
    event_type = event.get('type', '')

    if event_type == 'checkout.session.completed':
        _handle_checkout_completed(event['data']['object'])

    elif event_type == 'payment_intent.payment_failed':
        pi = event['data']['object']
        logger.warning(
            f'Stripe: 決済失敗 payment_intent={pi.get("id")} '
            f'reason={pi.get("last_payment_error", {}).get("message", "")}'
        )

    else:
        logger.debug(f'Stripe Webhook: 未処理イベント {event_type}')

    return HttpResponse(status=200)


def _handle_checkout_completed(session):
    """checkout.session.completed を受けて ProduceOrder を決済済みにする"""
    from orders.models import ProduceOrder

    payment_intent_id = session.get('payment_intent', '')
    if not payment_intent_id:
        logger.warning('checkout.session.completed: payment_intent が空')
        return

    # メタデータに order_id を埋め込む設計を推奨するが、
    # 現状は payment_intent ID で突き合わせる
    updated = ProduceOrder.objects.filter(
        stripe_payment_intent=payment_intent_id
    ).update(is_paid=True, status='confirmed')

    if updated:
        logger.info(f'ProduceOrder 決済済みに更新: payment_intent={payment_intent_id}')
    else:
        logger.warning(
            f'checkout.session.completed: 対応する ProduceOrder が見つからない '
            f'payment_intent={payment_intent_id}'
        )
