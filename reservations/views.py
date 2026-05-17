from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Reservation, ReservationSeat
from accounts.models import Store

def reservation_create(request):
    if request.method == 'POST':
        try:
            # 日時の組み立て
            date_str = request.POST.get('selected_date', '')
            time_str = request.POST.get('selected_time', '')
            if not date_str or not time_str:
                messages.error(request, '来店日時を選択してください')
                return render(request, 'reservations/reservation_form.html')

            start_at = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
            start_at = timezone.make_aware(start_at)
            end_at_naive = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M').replace(hour=23, minute=0)
            end_at = timezone.make_aware(end_at_naive)

            # 基本情報
            guest_name  = request.POST.get('guest_name', '').strip()
            guest_phone = request.POST.get('guest_phone', '').strip()
            guest_email = request.POST.get('guest_email', '').strip()
            party_size  = int(request.POST.get('party_size', 1))
            notes_base  = request.POST.get('notes', '').strip()
            seat_pref   = request.POST.get('seat_preference', 'おまかせ')
            course      = request.POST.get('selected_course', '')

            if not guest_name or not guest_phone or not guest_email:
                messages.error(request, '必須項目を入力してください')
                return render(request, 'reservations/reservation_form.html')

            # 備考にコース・席希望を追記
            notes = f'【コース】{course}\n【席希望】{seat_pref}'
            if notes_base:
                notes += f'\n【備考】{notes_base}'

            store = Store.objects.get(slug='itadaki')

            reservation = Reservation.objects.create(
                store=store,
                guest_name=guest_name,
                guest_phone=guest_phone,
                guest_email=guest_email,
                party_size=party_size,
                start_at=start_at,
                end_at=end_at,
                channel=Reservation.Channel.WEB,
                notes=notes,
                status=Reservation.Status.PENDING,
            )

            messages.success(request, f'{guest_name}様のご予約を受け付けました。ありがとうございます。')
            return redirect('reservations:create')

        except Exception as e:
            messages.error(request, f'エラーが発生しました：{e}')
            return render(request, 'reservations/reservation_form.html')

    return render(request, 'reservations/reservation_form.html')


from django.contrib.auth.decorators import login_required
from .forms import StaffReservationForm
from .models import Seat, SeatSection

@login_required
def staff_reservation_create(request):
    store = Store.objects.get(slug='itadaki')
    seat_qs = Seat.objects.filter(section__store=store, is_active=True).order_by('section__sort_order', 'sort_order')

    if request.method == 'POST':
        form = StaffReservationForm(request.POST)
        form.fields['seats'].queryset = seat_qs
        if form.is_valid():
            cd = form.cleaned_data
            start_at = timezone.make_aware(
                datetime.combine(cd['visit_date'], cd['visit_time'])
            )
            end_at = start_at.replace(hour=23, minute=0, second=0)
            reservation = Reservation.objects.create(
                store=store,
                guest_name=cd['guest_name'],
                guest_phone=cd.get('guest_phone', ''),
                guest_email=cd.get('guest_email', ''),
                party_size=cd['party_size'],
                start_at=start_at,
                end_at=end_at,
                channel=cd['channel'],
                notes=cd.get('notes', ''),
                staff_memo=cd.get('staff_memo', ''),
                status='confirmed',
                assigned_staff=request.user,
            )
            for seat in cd.get('seats') or []:
                ReservationSeat.objects.create(reservation=reservation, seat=seat)
            messages.success(request, f'✅ {cd["guest_name"]}様の予約を登録しました。')
            return redirect('reservations:staff_create')
    else:
        form = StaffReservationForm()
        form.fields['seats'].queryset = seat_qs

    seats_by_section = {}
    for seat in seat_qs:
        seats_by_section.setdefault(seat.section.name, []).append(seat)

    return render(request, 'reservations/staff_reservation_form.html', {
        'form': form,
        'seats_by_section': seats_by_section,
        'store': store,
    })


@login_required
def staff_reservation_list(request):
    store = Store.objects.get(slug='itadaki')
    date_str = request.GET.get('date', '')
    from datetime import date
    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            filter_date = date.today()
    else:
        filter_date = date.today()

    reservations = Reservation.objects.filter(
        store=store,
        start_at__date=filter_date,
    ).prefetch_related('reservation_seats__seat').order_by('start_at')

    return render(request, 'reservations/staff_reservation_list.html', {
        'reservations': reservations,
        'filter_date': filter_date,
        'store': store,
    })


@login_required
def staff_floor_map(request):
    from datetime import date
    store = Store.objects.get(slug='itadaki')
    today = date.today()

    # 今日の確定・着席中の予約を取得
    active_reservations = Reservation.objects.filter(
        store=store,
        start_at__date=today,
        status__in=['confirmed', 'seated'],
    ).prefetch_related('reservation_seats__seat')

    # 席ごとのステータスを辞書で作成
    seat_status = {}  # seat.pk -> [{'status': ..., 'reservation': ...}, ...]
    for r in active_reservations:
        for rs in r.reservation_seats.all():
            seat_status.setdefault(rs.seat.pk, []).append({
                'status': r.status,
                'reservation': r,
            })

    # セクション別に席を整理
    sections = SeatSection.objects.filter(store=store).prefetch_related(
        'seats'
    ).order_by('sort_order')

    sections_data = []
    for section in sections:
        seats_data = []
        for seat in section.seats.filter(is_active=True).order_by('sort_order'):
            info = seat_status.get(seat.pk)



@login_required
def staff_floor_map(request):
    from datetime import date
    store = Store.objects.get(slug='itadaki')
    today = date.today()

    # 今日の確定・着席中の予約を取得
    active_reservations = Reservation.objects.filter(
        store=store,
        start_at__date=today,
        status__in=['confirmed', 'seated'],
    ).prefetch_related('reservation_seats__seat')

    # 席ごとのステータスを辞書で作成
    seat_status = {}  # seat.pk -> [{'status': ..., 'reservation': ...}, ...]
    for r in active_reservations:
        for rs in r.reservation_seats.all():
            seat_status.setdefault(rs.seat.pk, []).append({
                'status': r.status,
                'reservation': r,
            })

    # セクション別に席を整理
    sections = SeatSection.objects.filter(store=store).prefetch_related(
        'seats'
    ).order_by('sort_order')

    sections_data = []
    for section in sections:
        seats_data = []
        for seat in section.seats.filter(is_active=True).order_by('sort_order'):
            infos = seat_status.get(seat.pk, [])
            if infos:
                # 来店時間が早い順に並べる
                infos_sorted = sorted(infos, key=lambda x: x['reservation'].start_at)
                status = infos_sorted[0]['status']
                reservations = [i['reservation'] for i in infos_sorted]
            else:
                status = 'empty'
                reservations = []
            seats_data.append({
                'seat': seat,
                'status': status,
                'reservations': reservations,
            })
        sections_data.append({
            'section': section,
            'seats': seats_data,
        })

    return render(request, 'reservations/staff_floor_map.html', {
        'sections_data': sections_data,
        'store': store,
        'today': today,
    })


@login_required
def staff_reservation_detail(request, pk):
    from django.shortcuts import get_object_or_404
    store = Store.objects.get(slug='itadaki')
    reservation = get_object_or_404(Reservation, pk=pk, store=store)
    seat_qs = Seat.objects.filter(section__store=store, is_active=True).order_by('section__sort_order', 'sort_order')

    if request.method == 'POST':
        action = request.POST.get('action', '')

        # ステータス変更
        if action == 'status':
            new_status = request.POST.get('status', '')
            if new_status in dict(Reservation.STATUS_CHOICES):
                reservation.status = new_status
                reservation.save()
                messages.success(request, f'ステータスを「{reservation.get_status_display()}」に変更しました。')
            return redirect('reservations:staff_detail', pk=pk)

        # 予約内容編集
        if action == 'edit':
            form = StaffReservationForm(request.POST)
            form.fields['seats'].queryset = seat_qs
            if form.is_valid():
                cd = form.cleaned_data
                start_at = timezone.make_aware(
                    datetime.combine(cd['visit_date'], cd['visit_time'])
                )
                end_at = start_at.replace(hour=23, minute=0, second=0)
                reservation.guest_name  = cd['guest_name']
                reservation.guest_phone = cd.get('guest_phone', '')
                reservation.guest_email = cd.get('guest_email', '')
                reservation.party_size  = cd['party_size']
                reservation.start_at    = start_at
                reservation.end_at      = end_at
                reservation.channel     = cd['channel']
                reservation.notes       = cd.get('notes', '')
                reservation.staff_memo  = cd.get('staff_memo', '')
                reservation.save()
                # 席を更新
                reservation.reservation_seats.all().delete()
                for seat in cd.get('seats') or []:
                    ReservationSeat.objects.create(reservation=reservation, seat=seat)
                messages.success(request, '予約内容を更新しました。')
                return redirect('reservations:staff_detail', pk=pk)
        else:
            form = StaffReservationForm(initial={
                'channel':    reservation.channel,
                'visit_date': reservation.start_at.date(),
                'visit_time': reservation.start_at.strftime('%H:%M'),
                'party_size': reservation.party_size,
                'guest_name':  reservation.guest_name,
                'guest_phone': reservation.guest_phone,
                'guest_email': reservation.guest_email,
                'notes':       reservation.notes,
                'staff_memo':  reservation.staff_memo,
            })
            form.fields['seats'].queryset = seat_qs
    else:
        form = StaffReservationForm(initial={
            'channel':    reservation.channel,
            'visit_date': reservation.start_at.date(),
            'visit_time': reservation.start_at.strftime('%H:%M'),
            'party_size': reservation.party_size,
            'guest_name':  reservation.guest_name,
            'guest_phone': reservation.guest_phone,
            'guest_email': reservation.guest_email,
            'notes':       reservation.notes,
            'staff_memo':  reservation.staff_memo,
        })
        form.fields['seats'].queryset = seat_qs

    assigned_seat_pks = list(reservation.reservation_seats.values_list('seat_id', flat=True))
    seats_by_section = {}
    for seat in seat_qs:
        seats_by_section.setdefault(seat.section.name, []).append(seat)

    return render(request, 'reservations/staff_reservation_detail.html', {
        'reservation': reservation,
        'form': form,
        'seats_by_section': seats_by_section,
        'assigned_seat_pks': assigned_seat_pks,
        'store': store,
        'status_choices': Reservation.STATUS_CHOICES,
    })
