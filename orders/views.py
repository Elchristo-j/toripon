<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>予約管理 | {{ store.name }}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #f0e8f5; font-family: -apple-system, BlinkMacSystemFont, 'Hiragino Sans', sans-serif; min-height: 100vh; overflow-x: hidden; }

    .header { background: #4a1a6e; padding: 1rem 1.25rem; display: flex; align-items: center; justify-content: space-between; }
    .header-title { color: #f0e0ff; font-size: 16px; font-weight: 500; }
    .header-sub { color: #c8a8e0; font-size: 11px; margin-top: 2px; }
    .badge-new { background: #e8331a; color: #fff; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 500; }

    .body { padding: 1rem; max-width: 480px; margin: 0 auto; }

    /* タブ */
    .tab-row { display: flex; gap: 6px; margin-bottom: 1rem; }
    .tab { flex: 1; padding: 8px 4px; border-radius: 8px; border: 0.5px solid #c9a8d8; background: #fff; text-align: center; font-size: 12px; color: #6b3a8a; cursor: pointer; }
    .tab.active { background: #4a1a6e; border-color: #4a1a6e; color: #e8c8f5; }

    /* 予約カード */
    .order-card { background: #fff; border-radius: 12px; border: 0.5px solid #c9a8d8; padding: 1rem; margin-bottom: 10px; position: relative; }
    .order-card.status-pending  { border-left: 4px solid #e8a020; }
    .order-card.status-confirmed { border-left: 4px solid #2d7a4a; }
    .order-card.status-rejected { border-left: 4px solid #a83030; opacity: 0.6; }

    /* 種別ラベル */
    .type-label { display: inline-block; font-size: 10px; border-radius: 4px; padding: 2px 7px; margin-bottom: 6px; font-weight: 500; }
    .type-label.visit    { background: #e8f0ff; color: #2a4a9a; }
    .type-label.delivery { background: #fff0e0; color: #9a5010; }

    .card-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 8px; }
    .customer-name { font-size: 15px; font-weight: 500; color: #2d1040; }
    .date-line { font-size: 13px; color: #6b3a8a; margin-top: 2px; }
    .status-badge { font-size: 11px; border-radius: 6px; padding: 3px 8px; font-weight: 500; white-space: nowrap; }
    .status-badge.pending   { background: #fef3e0; color: #a86010; }
    .status-badge.confirmed { background: #e0f5e9; color: #1a5c35; }
    .status-badge.rejected  { background: #fdf0f0; color: #a83030; }

    .items-list { background: #f7f0fa; border-radius: 8px; padding: 8px 10px; margin-bottom: 10px; }
    .item-row { display: flex; justify-content: space-between; font-size: 13px; color: #2d1040; padding: 2px 0; }
    .item-total { font-size: 13px; font-weight: 500; color: #4a1a6e; border-top: 0.5px solid #d4aee8; margin-top: 4px; padding-top: 4px; text-align: right; }

    .customer-info { font-size: 12px; color: #6b3a8a; margin-bottom: 10px; line-height: 1.8; }
    .payment-label { display: inline-block; font-size: 11px; background: #f0ddf7; color: #6b3a8a; border-radius: 4px; padding: 2px 7px; }

    /* 届け先ブロック（配送のみ） */
    .delivery-detail { background: #fff8f0; border: 0.5px solid #e8c8a0; border-radius: 8px; padding: 8px 10px; margin-bottom: 10px; font-size: 12px; color: #5a3010; line-height: 1.8; }
    .delivery-detail .detail-title { font-size: 10px; font-weight: 600; color: #9a5010; margin-bottom: 4px; letter-spacing: 0.05em; }

    .note-box { background: #f0f0f0; border-radius: 6px; padding: 6px 10px; font-size: 12px; color: #444; margin-bottom: 10px; }

    .action-row { display: flex; gap: 8px; }
    .btn-ok { flex: 1; background: #2d5a3d; color: #c8f0d8; border: none; border-radius: 8px; padding: 10px; font-size: 13px; font-weight: 500; cursor: pointer; }
    .btn-ng { flex: 1; background: #fff; color: #a83030; border: 0.5px solid #e8b0b0; border-radius: 8px; padding: 10px; font-size: 13px; cursor: pointer; }
    .btn-ok:disabled, .btn-ng:disabled { opacity: 0.4; cursor: not-allowed; }

    .empty { text-align: center; padding: 3rem 1rem; color: #9a6ab0; font-size: 14px; }

    .toast { position: fixed; top: 1rem; left: 50%; transform: translateX(-50%); background: #4a1a6e; color: #e8c8f5; padding: 10px 20px; border-radius: 10px; font-size: 13px; display: none; z-index: 999; white-space: nowrap; }
    .toast.show { display: block; }

    .refresh-info { text-align: center; font-size: 11px; color: #9a6ab0; margin-bottom: 1rem; }
  </style>
</head>
<body>

<div class="header">
  <div>
    <div class="header-title">🍇 {{ store.name }} 予約管理</div>
    <div class="header-sub">30秒ごとに自動更新</div>
  </div>
  {% if pending_count > 0 %}
  <div class="badge-new">{{ pending_count }}</div>
  {% endif %}
</div>

<div class="body">
  <div class="tab-row">
    <div class="tab active" id="tab-pending"  onclick="switchTab('pending')">未確認 ({{ pending_count }})</div>
    <div class="tab" id="tab-visit"    onclick="switchTab('visit')">🚶 来店</div>
    <div class="tab" id="tab-delivery" onclick="switchTab('delivery')">📦 配送</div>
    <div class="tab" id="tab-all"      onclick="switchTab('all')">すべて</div>
  </div>

  <div class="refresh-info">次回更新まで <span id="countdown">30</span> 秒</div>

  <div id="orders-container">
    {% for order in orders %}
    <div class="order-card status-{{ order.status }}"
         id="card-{{ order.id }}"
         data-status="{{ order.status }}"
         data-type="{{ order.order_type }}">

      <!-- 種別ラベル -->
      {% if order.order_type == 'delivery' %}
      <div class="type-label delivery">📦 贈答・配送</div>
      {% else %}
      <div class="type-label visit">🚶 来店受取</div>
      {% endif %}

      <div class="card-header">
        <div>
          <div class="customer-name">{{ order.customer_name }}</div>
          {% if order.order_type == 'delivery' %}
          <div class="date-line">🚚 希望配送日：{{ order.delivery_date|date:"m月d日" }}</div>
          {% else %}
          <div class="date-line">📅 来店予定日：{{ order.visit_date|date:"m月d日（D）" }}</div>
          {% endif %}
        </div>
        <div class="status-badge {{ order.status }}">
          {% if order.status == 'pending' %}未確認
          {% elif order.status == 'confirmed' %}OK
          {% elif order.status == 'rejected' %}お断り
          {% endif %}
        </div>
      </div>

      <!-- 注文品目 -->
      <div class="items-list">
        {% for item in order.produce_items.all %}
        <div class="item-row">
          <span>{{ item.menu_item.name }}</span>
          <span>{{ item.quantity }}{{ item.menu_item.unit }} × ¥{{ item.menu_item.price|floatformat:0 }}</span>
        </div>
        {% endfor %}
        <div class="item-total">合計 ¥{{ order.total_price|floatformat:0 }}</div>
      </div>

      <!-- 申込者情報 -->
      <div class="customer-info">
        📞 {{ order.customer_phone }}<br>
        ✉️ {{ order.customer_email }}<br>
        <span class="payment-label">{{ order.get_payment_method_display }}</span>
      </div>

      <!-- 配送のみ：送り主・届け先 -->
      {% if order.order_type == 'delivery' %}
      <div class="delivery-detail">
        <div class="detail-title">送り主</div>
        {{ order.sender_name }}　{{ order.sender_phone }}<br>
        〒{{ order.sender_postal_code }}　{{ order.sender_address }}
      </div>
      <div class="delivery-detail">
        <div class="detail-title">届け先</div>
        {{ order.receiver_name }}　{{ order.receiver_phone }}<br>
        〒{{ order.postal_code }}　{{ order.address }}
      </div>
      {% endif %}

      <!-- 特記事項 -->
      {% if order.note %}
      <div class="note-box">📝 {{ order.note }}</div>
      {% endif %}

      {% if order.status == 'pending' %}
      <div class="action-row">
        <button class="btn-ok" onclick="doAction({{ order.id }}, 'confirmed')">✅ OK・受け付ける</button>
        <button class="btn-ng" onclick="doAction({{ order.id }}, 'rejected')">❌ お断り</button>
      </div>
      {% endif %}
    </div>
    {% empty %}
    <div class="empty">予約・注文はまだありません</div>
    {% endfor %}
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
  let currentTab = 'pending';

  function switchTab(tab) {
    currentTab = tab;
    ['pending', 'visit', 'delivery', 'all'].forEach(t => {
      document.getElementById('tab-' + t).className = 'tab' + (t === tab ? ' active' : '');
    });
    document.querySelectorAll('.order-card').forEach(card => {
      const status = card.dataset.status;
      const type   = card.dataset.type;
      let show = false;
      if (tab === 'all')      show = true;
      else if (tab === 'pending')  show = status === 'pending';
      else if (tab === 'visit')    show = type === 'visit';
      else if (tab === 'delivery') show = type === 'delivery';
      card.style.display = show ? 'block' : 'none';
    });
  }
  switchTab('pending');

  function doAction(orderId, action) {
    const card = document.getElementById('card-' + orderId);
    card.querySelectorAll('button').forEach(b => b.disabled = true);
    fetch('/orders/produce/staff/action/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ order_id: orderId, action: action }),
    })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        showToast(action === 'confirmed' ? '✅ 受け付けました。メールを送信しました。' : '❌ お断りメールを送信しました。');
        setTimeout(() => location.reload(), 1500);
      } else {
        showToast('エラーが発生しました');
        card.querySelectorAll('button').forEach(b => b.disabled = false);
      }
    });
  }

  function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 3000);
  }

  let countdown = 30;
  setInterval(() => {
    countdown--;
    document.getElementById('countdown').textContent = countdown;
    if (countdown <= 0) location.reload();
  }, 1000);

  // 新規予約通知音
  function playBeep() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.frequency.value = 880;
      g.gain.setValueAtTime(0.3, ctx.currentTime);
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      o.start(ctx.currentTime);
      o.stop(ctx.currentTime + 0.5);
    } catch(e) {}
  }

  const newCount = {{ pending_count }};
  const lastCount = parseInt(sessionStorage.getItem('lastPendingCount') || '0');
  if (newCount > lastCount) { playBeep(); }
  sessionStorage.setItem('lastPendingCount', newCount);

  function getCookie(name) {
    const v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
    return v ? v[2] : '';
  }
</script>
</body>
</html>
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

    # 権限によってフィルター条件を切り替え
    if user.role in ADMIN_ROLES:
        store_filter = {}
        order_filter = {}
    else:
        store_filter = {'order__store': user.store}
        order_filter = {'store': user.store}

    today = timezone.localdate()
    now   = timezone.now()

    # ── 今日の注文（closedのみ = 会計済み）
    today_closed = Order.objects.filter(
        created_at__date=today,
        status='closed',
        **order_filter
    )
    # ── 今日の未会計（open）
    today_open = Order.objects.filter(
        created_at__date=today,
        status='open',
        **order_filter
    )

    # ── 正確な売上（price × quantity）
    today_sales = OrderItem.objects.filter(
        order__created_at__date=today,
        order__status='closed',
        **store_filter
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
        order__status='open',
        **store_filter
    ).aggregate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )['total'] or 0
    unpaid_count = today_open.count()

    # ── 昨日の売上（比較用）
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

    # ── 席別売上（本日）
    seat_sales_qs = OrderItem.objects.filter(
        order__created_at__date=today,
        **store_filter
    ).values('order__seat_code', 'order__status').annotate(
        total=Sum(F('menu_item__price') * F('quantity'))
    )

    # 全席リスト（頂の固定席）
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

    # ── 本日のメニューランキング（カテゴリ別 TOP5）
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

    # ── 月間・累計
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

    # ── 直近7日間の売上（グラフ用）
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

    # ── 先週のランキング（戦略用）
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
    """生産者向け予約管理画面"""
    user = request.user
    if user.role in ADMIN_ROLES:
        store = None
        from .models import ProduceOrder
        orders = ProduceOrder.objects.prefetch_related('produce_items__menu_item').all()
    else:
        store = user.store
        from .models import ProduceOrder
        orders = ProduceOrder.objects.filter(store=store).prefetch_related('produce_items__menu_item')

    pending_count   = orders.filter(status='pending').count()
    confirmed_count = orders.filter(status='confirmed').count()

    return render(request, 'orders/produce_staff_list.html', {
        'store': store or user.store,
        'orders': orders,
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

    # 返信メール送信
    store_name = order.store.name
    customer_name = order.customer_name
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
    from .models import ProduceOrder, ProduceOrderItem
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


def top(request):
    stores = Store.objects.filter(is_active=True).order_by('created_at')
    return render(request, 'orders/top.html', {'stores': stores})


def delivery_order_form(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, is_active=True)
    menu_items = MenuItem.objects.filter(category__store=store, is_available=True)
    return render(request, 'orders/delivery_order_form.html', {
        'store': store,
        'menu_items': menu_items,
    })


def delivery_order_submit(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, is_active=True)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '不正なリクエストです'})
    customer_name = data.get('customer_name', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    customer_email = data.get('customer_email', '').strip()
    delivery_date = data.get('delivery_date', '').strip()
    payment_method = data.get('payment_method', 'bank')
    note = data.get('note', '').strip()
    items = data.get('items', [])
    sender_name = data.get('sender_name', '').strip()
    sender_phone = data.get('sender_phone', '').strip()
    sender_postal_code = data.get('sender_postal_code', '').strip()
    sender_address = data.get('sender_address', '').strip()
    receiver_name = data.get('receiver_name', '').strip()
    receiver_phone = data.get('receiver_phone', '').strip()
    postal_code = data.get('postal_code', '').strip()
    address = data.get('address', '').strip()
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


def delivery_order_form(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, is_active=True)
    menu_items = MenuItem.objects.filter(category__store=store, is_available=True)
    return render(request, 'orders/delivery_order_form.html', {
        'store': store,
        'menu_items': menu_items,
    })


def delivery_order_submit(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, is_active=True)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '不正なリクエストです'})
    customer_name = data.get('customer_name', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    customer_email = data.get('customer_email', '').strip()
    delivery_date = data.get('delivery_date', '').strip()
    payment_method = data.get('payment_method', 'bank')
    note = data.get('note', '').strip()
    items = data.get('items', [])
    sender_name = data.get('sender_name', '').strip()
    sender_phone = data.get('sender_phone', '').strip()
    sender_postal_code = data.get('sender_postal_code', '').strip()
    sender_address = data.get('sender_address', '').strip()
    receiver_name = data.get('receiver_name', '').strip()
    receiver_phone = data.get('receiver_phone', '').strip()
    postal_code = data.get('postal_code', '').strip()
    address = data.get('address', '').strip()
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
