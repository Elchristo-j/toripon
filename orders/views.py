from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json

from .models import MenuCategory, MenuItem, Order, OrderItem
from reservations.models import Seat
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncHour
from datetime import timedelta

def order_menu(request, seat_code):
    seat = get_object_or_404(Seat, code=seat_code)
    categories = MenuCategory.objects.prefetch_related('items').all()

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
    orders = Order.objects.filter(status='open').prefetch_related(
        'items__menu_item'
    ).order_by('created_at')

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
    today = timezone.localdate()
    now   = timezone.now()
 
    # ── 今日の注文（closedのみ = 会計済み）
    today_closed = Order.objects.filter(
        created_at__date=today,
        status='closed'
    )
    # ── 今日の未会計（open）
    today_open = Order.objects.filter(
        created_at__date=today,
        status='open'
    )
 
    # ── 今日の売上合計

 
    # ── 正確な売上（price × quantity）
    from django.db.models import F
    today_sales = OrderItem.objects.filter(
        order__created_at__date=today,
        order__status='closed'
    ).aggregate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )['total'] or 0
 
    # ── 今日の注文件数
    today_order_count = today_closed.count()
 
    # ── 客単価
    avg_per_order = int(today_sales / today_order_count) if today_order_count else 0
 
    # ── 未会計の合計金額と席数
    unpaid_total = OrderItem.objects.filter(
        order__created_at__date=today,
        order__status='open'
    ).aggregate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )['total'] or 0
    unpaid_count = today_open.count()
 
    # ── 昨日の売上（比較用）
    yesterday = today - timedelta(days=1)
    yesterday_sales = OrderItem.objects.filter(
        order__created_at__date=yesterday,
        order__status='closed'
    ).aggregate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )['total'] or 0
 
    if yesterday_sales > 0:
        day_over_day = round((today_sales - yesterday_sales) / yesterday_sales * 100, 1)
    else:
        day_over_day = None  # 昨日データなし
 
    # ── 席別売上（本日）
    # seat_codeごとに集計
    seat_sales_qs = OrderItem.objects.filter(
        order__created_at__date=today
    ).values('order__seat_code', 'order__status').annotate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )
 
    # 全席リスト（頂の固定席）
    ALL_SEATS = ['C-1','C-2','C-3','C-4','C-5','C-6',
                 'T-1','T-2','T-3',
                 'K-1','K-2','K-3','K-4']
 
    # 席ごとに状態と金額をまとめる
    seat_dict = {s: {'total': 0, 'status': 'unused'} for s in ALL_SEATS}
    for row in seat_sales_qs:
        code = row['order__seat_code']
        if code in seat_dict:
            seat_dict[code]['total'] += row['total'] or 0
            # open が1件でもあれば unpaid
            if row['order__status'] == 'open':
                seat_dict[code]['status'] = 'open'
            elif seat_dict[code]['status'] == 'unused':
                seat_dict[code]['status'] = 'closed'
 
    seat_list = [
        {'code': code, 'status': data['status'], 'total': data['total']}
        for code, data in seat_dict.items()
    ]
 
    # ── 本日のメニューランキング（カテゴリ別 TOP5）
    drink_ranking = OrderItem.objects.filter(
        order__created_at__date=today,
        menu_item__category__name__in=['ドリンク', 'drink', 'drinks']
    ).values('menu_item__name').annotate(
        cnt=Sum('quantity')
    ).order_by('-cnt')[:5]
 
    food_ranking = OrderItem.objects.filter(
        order__created_at__date=today,
    ).exclude(
        menu_item__category__name__in=['ドリンク', 'drink', 'drinks']
    ).values('menu_item__name').annotate(
        cnt=Sum('quantity')
    ).order_by('-cnt')[:5]
 
    # ── 月間・累計
    month_start = today.replace(day=1)
    month_sales = OrderItem.objects.filter(
        order__created_at__date__gte=month_start,
        order__status='closed'
    ).aggregate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )['total'] or 0
 
    month_order_count = Order.objects.filter(
        created_at__date__gte=month_start,
        status='closed'
    ).count()
 
    year_start = today.replace(month=1, day=1)
    year_sales = OrderItem.objects.filter(
        order__created_at__date__gte=year_start,
        order__status='closed'
    ).aggregate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )['total'] or 0
 
    # ── 直近7日間の売上（グラフ用）
    weekly_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        s = OrderItem.objects.filter(
            order__created_at__date=d,
            order__status='closed'
        ).aggregate(
            total=Sum(F('menu_item__price') * F('quantity'))
        )['total'] or 0
        weekly_data.append({'date': d.strftime('%-m/%-d'), 'sales': int(s)})
 
    # ── 先週のランキング（戦略用）
    last_week_start = today - timedelta(days=today.weekday() + 7)
    last_week_end   = last_week_start + timedelta(days=6)
 
    last_drink_ranking = OrderItem.objects.filter(
        order__created_at__date__range=[last_week_start, last_week_end],
        order__status='closed',
        menu_item__category__name__in=['ドリンク', 'drink', 'drinks']
    ).values('menu_item__name').annotate(cnt=Sum('quantity')).order_by('-cnt')[:5]
 
    last_food_ranking = OrderItem.objects.filter(
        order__created_at__date__range=[last_week_start, last_week_end],
        order__status='closed',
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
 