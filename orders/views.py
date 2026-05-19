from accounts.models import Store
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json

from .models import MenuCategory, MenuItem, Order, OrderItem
from reservations.models import Seat
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate, TruncHour
from datetime import timedelta

# 管理者ロール（全店舗データを閲覧可能）
ADMIN_ROLES = ['chief_administrator', 'administrator']


def order_menu(request, seat_code, store_slug=None):
    seat = get_object_or_404(Seat, code=seat_code)
    categories = MenuCategory.objects.prefetch_related('items').filter(
        store__slug=store_slug
    ) if store_slug else MenuCategory.objects.prefetch_related('items').all()
    session_key = f'order_id_{seat_code}'
    order_id = request.session.get(session_key)

    if order_id:
        try:
            order = Order.objects.get(id=order_id, status='open')
        except Order.DoesNotExist:
            order = Order.objects.create(seat_code=seat_code, status='open')
            request.session[session_key] = order.id
    else:
        order = Order.objects.create(seat_code=seat_code, status='open')
        request.session[session_key] = order.id

    context = {
        'seat': seat,
        'categories': categories,
        'order': order,
    }
    return render(request, 'orders/menu.html', context)


@require_POST
def order_submit(request):
    data = json.loads(request.body)
    order_id = data.get('order_id')
    items = data.get('items', [])

    order = get_object_or_404(Order, id=order_id)

    for item_data in items:
        menu_item = get_object_or_404(MenuItem, id=item_data['menu_item_id'])
        OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=item_data['quantity'],
            status='pending',
        )

    return JsonResponse({'success': True})


@login_required
def staff_order_list(request):
    user = request.user

    if user.role in ADMIN_ROLES:
        orders = Order.objects.filter(status='open')
    else:
        orders = Order.objects.filter(status='open', store=user.store)

    orders = orders.prefetch_related('items__menu_item').order_by('created_at')

    context = {
        'orders': orders,
    }
    return render(request, 'orders/staff_order_list.html', context)


@login_required
@require_POST
def staff_order_merge(request):
    data = json.loads(request.body)
    order_ids = data.get('order_ids', [])

    if len(order_ids) < 2:
        return JsonResponse({'success': False, 'error': '2件以上選択してください'})

    import uuid
    group_id = str(uuid.uuid4())[:8]

    Order.objects.filter(id__in=order_ids).update(group_id=group_id)

    return JsonResponse({'success': True, 'group_id': group_id})


@login_required
@require_POST
def staff_order_close(request):
    data = json.loads(request.body)
    order_id = data.get('order_id')
    group_id = data.get('group_id')

    if group_id:
        Order.objects.filter(group_id=group_id).update(status='closed')
    else:
        Order.objects.filter(id=order_id).update(status='closed')

    return JsonResponse({'success': True})


@login_required
def dashboard(request):
    """売上ダッシュボード"""
    user = request.user

    if user.role in ADMIN_ROLES:
        store_filter = {}
        order_filter = {}
    else:
        store_filter = {'order__store': user.store}
        order_filter = {'store': user.store}

    today = timezone.localdate()
    now   = timezone.now()

    today_closed = Order.objects.filter(
        created_at__date=today,
        status='closed',
        **order_filter
    )
    today_open = Order.objects.filter(
        created_at__date=today,
        status='open',
        **order_filter
    )

    today_sales = OrderItem.objects.filter(
        order__created_at__date=today,
        order__status='closed',
        **store_filter
    ).aggregate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )['total'] or 0

    today_order_count = today_closed.count()
    avg_per_order = int(today_sales / today_order_count) if today_order_count else 0

    unpaid_total = OrderItem.objects.filter(
        order__created_at__date=today,
        order__status='open',
        **store_filter
    ).aggregate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )['total'] or 0
    unpaid_count = today_open.count()

    yesterday = today - timedelta(days=1)
    yesterday_sales = OrderItem.objects.filter(
        order__created_at__date=yesterday,
        order__status='closed',
        **store_filter
    ).aggregate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )['total'] or 0

    if yesterday_sales > 0:
        day_over_day = round((today_sales - yesterday_sales) / yesterday_sales * 100, 1)
    else:
        day_over_day = None

    seat_sales_qs = OrderItem.objects.filter(
        order__created_at__date=today,
        **store_filter
    ).values('order__seat_code', 'order__status').annotate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )

    ALL_SEATS = ['C-1','C-2','C-3','C-4','C-5','C-6',
                 'T-1','T-2','T-3',
                 'K-1','K-2','K-3','K-4']

    seat_dict = {s: {'total': 0, 'status': 'unused'} for s in ALL_SEATS}
    for row in seat_sales_qs:
        code = row['order__seat_code']
        if code in seat_dict:
            seat_dict[code]['total'] += row['total'] or 0
            if row['order__status'] == 'open':
                seat_dict[code]['status'] = 'open'
            elif seat_dict[code]['status'] == 'unused':
                seat_dict[code]['status'] = 'closed'

    seat_list = [
        {'code': code, 'status': data['status'], 'total': data['total']}
        for code, data in seat_dict.items()
    ]

    drink_ranking = OrderItem.objects.filter(
        order__created_at__date=today,
        menu_item__category__name__in=['ドリンク', 'drink', 'drinks'],
        **store_filter
    ).values('menu_item__name').annotate(
        cnt=Sum('quantity')
    ).order_by('-cnt')[:5]

    food_ranking = OrderItem.objects.filter(
        order__created_at__date=today,
        **store_filter
    ).exclude(
        menu_item__category__name__in=['ドリンク', 'drink', 'drinks']
    ).values('menu_item__name').annotate(
        cnt=Sum('quantity')
    ).order_by('-cnt')[:5]

    month_start = today.replace(day=1)
    month_sales = OrderItem.objects.filter(
        order__created_at__date__gte=month_start,
        order__status='closed',
        **store_filter
    ).aggregate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )['total'] or 0

    month_order_count = Order.objects.filter(
        created_at__date__gte=month_start,
        status='closed',
        **order_filter
    ).count()

    year_start = today.replace(month=1, day=1)
    year_sales = OrderItem.objects.filter(
        order__created_at__date__gte=year_start,
        order__status='closed',
        **store_filter
    ).aggregate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )['total'] or 0

    weekly_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        s = OrderItem.objects.filter(
            order__created_at__date=d,
            order__status='closed',
            **store_filter
        ).aggregate(
            total=Sum(F('menu_item__price') * F('quantity'))
        )['total'] or 0
        weekly_data.append({'date': d.strftime('%-m/%-d'), 'sales': int(s)})

    last_week_start = today - timedelta(days=today.weekday() + 7)
    last_week_end   = last_week_start + timedelta(days=6)

    last_drink_ranking = OrderItem.objects.filter(
        order__created_at__date__range=[last_week_start, last_week_end],
        order__status='closed',
        menu_item__category__name__in=['ドリンク', 'drink', 'drinks'],
        **store_filter
    ).values('menu_item__name').annotate(cnt=Sum('quantity')).order_by('-cnt')[:5]

    last_food_ranking = OrderItem.objects.filter(
        order__created_at__date__range=[last_week_start, last_week_end],
        order__status='closed',
        **store_filter
    ).exclude(
        menu_item__category__name__in=['ドリンク', 'drink', 'drinks']
    ).values('menu_item__name').annotate(cnt=Sum('quantity')).order_by('-cnt')[:5]

    context = {
        'today': today,
        'today_sales': today_sales,
        'today_order_count': today_order_count,
        'avg_per_order': avg_per_order,
        'unpaid_count': unpaid_count,
        'unpaid_total': unpaid_total,
        'day_over_day': day_over_day,
        'seat_list': seat_list,
        'drink_ranking': list(drink_ranking),
        'food_ranking': list(food_ranking),
        'month_sales': month_sales,
        'month_order_count': month_order_count,
        'year_sales': year_sales,
        'weekly_data': json.dumps(weekly_data, ensure_ascii=False),
        'last_drink_ranking': list(last_drink_ranking),
        'last_food_ranking': list(last_food_ranking),
    }
    return render(request, 'orders/dashboard.html', context)


@login_required
def produce_staff_list(request):
    """生産者向け予約・注文管理画面（来店 + 配送）"""
    from .models import ProduceOrder
    user = request.user

    if user.role in ADMIN_ROLES:
        store = None
        orders = ProduceOrder.objects.prefetch_related('produce_items__menu_item').all()
    else:
        store = user.store
        orders = ProduceOrder.objects.filter(store=store).prefetch_related('produce_items__menu_item')

    pending_count   = orders.filter(status='pending').count()
    confirmed_count = orders.filter(status='confirmed').count()

    return render(request, 'orders/produce_staff_list.html', {
        'store': store or user.store,
        'orders': orders.order_by('-created_at'),
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
    })


@login_required
@require_POST
def produce_staff_action(request):
    """予約のOK/NGアクション＋返信メール送信"""
    from .models import ProduceOrder
    from django.core.mail import send_mail
    from django.conf import settings

    data = json.loads(request.body)
    order_id = data.get('order_id')
    action   = data.get('action')

    order = get_object_or_404(ProduceOrder, id=order_id)
    if action not in ['confirmed', 'rejected']:
        return JsonResponse({'success': False, 'error': '不正なアクションです'})

    order.status = action
    order.save()

    store_name    = order.store.name
    customer_name = order.customer_name

    if order.order_type == 'delivery':
        date_str = order.delivery_date.strftime('%m月%d日') if order.delivery_date else ''
        if action == 'confirmed':
            subject = f'【{store_name}】ご注文を受け付けました'
            message = (
                f'{customer_name} 様\n\n'
                f'贈答用ぶどうのご注文（希望配送日：{date_str}）を受け付けました。\n'
                f'お支払方法についてのご案内を別途送付いたします。\n\n'
                f'{store_name}'
            )
        else:
            subject = f'【{store_name}】ご注文について'
            message = (
                f'{customer_name} 様\n\n'
                f'誠に申し訳ございませんが、ご希望の品種・数量の在庫が確保できない状況です。\n'
                f'またのご注文をお待ちしております。\n\n'
                f'{store_name}'
            )
    else:
        visit_date = order.visit_date.strftime('%m月%d日') if order.visit_date else ''
        if action == 'confirmed':
            subject = f'【{store_name}】ご予約を受け付けました'
            message = (
                f'{customer_name} 様\n\n'
                f'{visit_date}のご予約を受け付けました。\n'
                f'当日お待ちしております。\n\n'
                f'キャンセルの場合はお電話にてご連絡ください。\n\n'
                f'{store_name}'
            )
        else:
            subject = f'【{store_name}】ご予約について'
            message = (
                f'{customer_name} 様\n\n'
                f'{visit_date}のご予約ですが、誠に申し訳ございません。\n'
                f'本日は予約でいっぱいとなっております。\n'
                f'またのご予約をお待ちしております。\n\n'
                f'{store_name}'
            )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.customer_email],
            fail_silently=True,
        )
    except Exception:
        pass

    return JsonResponse({'success': True})


def produce_order_form(request, store_slug):
    """ぶどう園来店予約フォーム（お客さん向け）"""
    store = get_object_or_404(Store, slug=store_slug, is_active=True)
    menu_items = MenuItem.objects.filter(
        category__store=store,
        is_available=True,
    ).order_by('order')
    return render(request, 'orders/produce_order_form.html', {
        'store': store,
        'menu_items': menu_items,
    })


@require_POST
def produce_order_submit(request, store_slug):
    """ぶどう園来店予約の送信処理"""
    store = get_object_or_404(Store, slug=store_slug, is_active=True)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '不正なリクエストです'})

    visit_date     = data.get('visit_date', '').strip()
    customer_name  = data.get('customer_name', '').strip()
    customer_email = data.get('customer_email', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    payment_method = data.get('payment_method', 'cash')
    items          = data.get('items', [])

    if not all([visit_date, customer_name, customer_email, customer_phone]):
        return JsonResponse({'success': False, 'error': '必須項目が入力されていません'})
    if not items:
        return JsonResponse({'success': False, 'error': '品種を1つ以上選んでください'})

    from .models import ProduceOrder, ProduceOrderItem
    order = ProduceOrder.objects.create(
        store=store,
        order_type='visit',
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        visit_date=visit_date,
        payment_method=payment_method,
        status='pending',
    )

    for item_data in items:
        menu_item = get_object_or_404(MenuItem, id=item_data['menu_item_id'])
        ProduceOrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=item_data['quantity'],
        )

    return JsonResponse({'success': True, 'order_id': order.id})


def delivery_order_form(request, store_slug):
    """贈答用配送注文フォーム（お客さん向け）"""
    store = get_object_or_404(Store, slug=store_slug, is_active=True)
    menu_items = MenuItem.objects.filter(
        category__store=store,
        is_available=True,
    ).order_by('order')
    return render(request, 'orders/delivery_order_form.html', {
        'store': store,
        'menu_items': menu_items,
    })


@require_POST
def delivery_order_submit(request, store_slug):
    """贈答用配送注文の送信処理"""
    store = get_object_or_404(Store, slug=store_slug, is_active=True)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '不正なリクエストです'})

    customer_name      = data.get('customer_name', '').strip()
    customer_phone     = data.get('customer_phone', '').strip()
    customer_email     = data.get('customer_email', '').strip()
    delivery_date      = data.get('delivery_date', '').strip()
    payment_method     = data.get('payment_method', 'bank')
    note               = data.get('note', '').strip()
    items              = data.get('items', [])
    sender_name        = data.get('sender_name', '').strip()
    sender_phone       = data.get('sender_phone', '').strip()
    sender_postal_code = data.get('sender_postal_code', '').strip()
    sender_address     = data.get('sender_address', '').strip()
    receiver_name      = data.get('receiver_name', '').strip()
    receiver_phone     = data.get('receiver_phone', '').strip()
    postal_code        = data.get('postal_code', '').strip()
    address            = data.get('address', '').strip()

    if not all([customer_name, customer_phone, customer_email, delivery_date]):
        return JsonResponse({'success': False, 'error': '必須項目が入力されていません'})
    if not all([sender_name, sender_phone, sender_postal_code, sender_address]):
        return JsonResponse({'success': False, 'error': '送り主情報を入力してください'})
    if not all([receiver_name, receiver_phone, postal_code, address]):
        return JsonResponse({'success': False, 'error': '届け先情報を入力してください'})
    if not items:
        return JsonResponse({'success': False, 'error': '品種を1つ以上選んでください'})

    from .models import ProduceOrder, ProduceOrderItem
    order = ProduceOrder.objects.create(
        store=store,
        order_type='delivery',
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        delivery_date=delivery_date,
        payment_method=payment_method,
        note=note,
        sender_name=sender_name,
        sender_phone=sender_phone,
        sender_postal_code=sender_postal_code,
        sender_address=sender_address,
        receiver_name=receiver_name,
        receiver_phone=receiver_phone,
        postal_code=postal_code,
        address=address,
        status='pending',
    )

    for item_data in items:
        menu_item = get_object_or_404(MenuItem, id=item_data['menu_item_id'])
        ProduceOrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=item_data['quantity'],
        )

    return JsonResponse({'success': True})


def top(request):
    stores = Store.objects.filter(is_active=True).order_by('created_at')
    return render(request, 'orders/top.html', {'stores': stores})
