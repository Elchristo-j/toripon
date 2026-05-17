from django.db import models
from django.conf import settings
from accounts.models import Store


class SeatSection(models.Model):
    SECTION_TYPE_CHOICES = [
        ('counter', 'カウンター'),
        ('table',   'テーブル'),
        ('kotatsu', '掘り炬燵'),
    ]
    store        = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='seat_sections', verbose_name='店舗')
    name         = models.CharField('セクション名', max_length=50)
    section_type = models.CharField('席タイプ', max_length=20, choices=SECTION_TYPE_CHOICES)
    description  = models.TextField('備考', blank=True)
    sort_order   = models.PositiveSmallIntegerField('表示順', default=0)

    class Meta:
        verbose_name = '席セクション'
        verbose_name_plural = '席セクション'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.store.name} / {self.name}'


class Seat(models.Model):
    section     = models.ForeignKey(SeatSection, on_delete=models.CASCADE, related_name='seats', verbose_name='セクション')
    code        = models.CharField('席コード', max_length=20)
    capacity    = models.PositiveSmallIntegerField('定員（人）')
    can_merge   = models.BooleanField('連結可能', default=False, help_text='掘り炬燵など複数ブロックを結合できる席に True を設定')
    is_active   = models.BooleanField('有効', default=True)
    description = models.TextField('備考', blank=True)
    sort_order  = models.PositiveSmallIntegerField('表示順', default=0)

    class Meta:
        verbose_name = '席'
        verbose_name_plural = '席'
        ordering = ['section__sort_order', 'sort_order', 'id']
        unique_together = [('section', 'code')]

    def __str__(self):
        return f'{self.section.name} / {self.code}'


class SeatLink(models.Model):
    seat_a      = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='links_as_a', verbose_name='席A')
    seat_b      = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='links_as_b', verbose_name='席B')
    description = models.CharField('備考', max_length=100, blank=True)

    class Meta:
        verbose_name = '席連結設定'
        verbose_name_plural = '席連結設定'
        unique_together = [('seat_a', 'seat_b')]


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending',   '仮予約（未確認）'),
        ('confirmed', '確定'),
        ('seated',    '着席中'),
        ('completed', '会計済み'),
        ('cancelled', 'キャンセル'),
        ('no_show',   '無断キャンセル'),
    ]
    CHANNEL_CHOICES = [
        ('web',        'Web予約'),
        ('phone',      '電話予約'),
        ('hotpepper',  'ホットペッパー'),
        ('tabelog',    '食べログ'),
        ('gate',       'GATE（イデアレコード）'),
        ('walk',       '飛び込み'),
        ('staff',      'スタッフ直接入力'),
    ]

    store          = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='reservations', verbose_name='店舗')
    guest_name     = models.CharField('予約者名', max_length=100)
    guest_phone    = models.CharField('電話番号', max_length=20, blank=True)
    guest_email    = models.EmailField('メールアドレス', blank=True)
    party_size     = models.PositiveSmallIntegerField('人数')
    start_at       = models.DateTimeField('来店日時')
    end_at         = models.DateTimeField('退席予定日時', help_text='AIが滞在時間と次の予約の重複を判定するために使用')
    status         = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='pending')
    channel        = models.CharField('予約経路', max_length=20, choices=CHANNEL_CHOICES, default='web')
    notes          = models.TextField('備考・要望', blank=True)
    staff_memo     = models.TextField('スタッフメモ', blank=True, default='')
    ai_check_result = models.JSONField('AI判定ログ', null=True, blank=True, help_text='Claude APIによる重複チェック結果をJSON形式で保存')
    assigned_staff = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_reservations', verbose_name='担当スタッフ')
    created_at     = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at     = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        verbose_name = '予約'
        verbose_name_plural = '予約'
        ordering = ['start_at']
        indexes = [
            models.Index(fields=['store', 'start_at']),
            models.Index(fields=['store', 'status']),
        ]

    def __str__(self):
        return f'{self.start_at:%Y-%m-%d %H:%M} {self.guest_name}様 ({self.party_size}名)'


class ReservationSeat(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='reservation_seats', verbose_name='予約')
    seat        = models.ForeignKey(Seat, on_delete=models.PROTECT, related_name='reservation_seats', verbose_name='席')
    is_primary  = models.BooleanField('主席フラグ', default=False, help_text='複数席のうち代表となる席（フロアマップ表示用）')

    class Meta:
        verbose_name = '予約席'
        verbose_name_plural = '予約席'
        unique_together = [('reservation', 'seat')]


class TimeSlot(models.Model):
    store      = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='time_slots', verbose_name='店舗')
    start_time = models.TimeField('開始時刻')
    label      = models.CharField('表示ラベル', max_length=20, blank=True, help_text='例: ディナー早め / ラストオーダー後 など')
    is_active  = models.BooleanField('有効', default=True)

    class Meta:
        verbose_name = '予約枠'
        verbose_name_plural = '予約枠'
        ordering = ['start_time']
        unique_together = [('store', 'start_time')]

    def __str__(self):
        return f'{self.start_time:%H:%M} {self.label}'
