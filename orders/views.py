from django.db import models
from accounts.models import Store


class MenuCategory(models.Model):
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE,
        related_name='menu_categories', verbose_name='店舗',
        null=True, blank=True
    )
    name = models.CharField('カテゴリ名', max_length=50)
    order = models.PositiveIntegerField('表示順', default=0)
    is_active = models.BooleanField('有効', default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'メニューカテゴリ'
        verbose_name_plural = 'メニューカテゴリ'

    def __str__(self):
        return f'{self.store.name} / {self.name}'


class MenuItem(models.Model):
    category = models.ForeignKey(
        MenuCategory, on_delete=models.CASCADE,
        related_name='items', verbose_name='カテゴリ'
    )
    name = models.CharField('メニュー名', max_length=100)
    description = models.TextField('説明', blank=True)
    price = models.PositiveIntegerField('価格（円）')
    image = models.ImageField('写真', upload_to='menu/', blank=True, null=True)
    is_available = models.BooleanField('提供中', default=True)
    order = models.PositiveIntegerField('表示順', default=0)
    badge = models.CharField('バッジ（例：人気No.1）', max_length=20, blank=True)
    image_url = models.URLField('画像URL（Cloudinary）', blank=True)
    unit = models.CharField('単位（例：房・袋）', max_length=10, default='房')

    class Meta:
        ordering = ['order']
        verbose_name = 'メニュー'
        verbose_name_plural = 'メニュー'

    def __str__(self):
        return f'{self.name}（{self.price}円）'


class Order(models.Model):
    STATUS_CHOICES = [
        ('open',   '注文中'),
        ('closed', '会計済み'),
    ]
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE,
        related_name='orders', verbose_name='店舗',
        null=True, blank=True
    )
    reservation = models.ForeignKey(
        'reservations.Reservation',
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    seat_code = models.CharField('席コード', max_length=20, blank=True, default='')
    group_id = models.CharField('グループID', max_length=50, blank=True, default='')
    status = models.CharField('ステータス', max_length=10,
                              choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)

    class Meta:
        verbose_name = '注文'
        verbose_name_plural = '注文'

    def __str__(self):
        return f'注文#{self.pk}（{self.seat_code}）'

    def total_price(self):
        return sum(item.subtotal() for item in self.items.all())


class OrderItem(models.Model):
    STATUS_CHOICES = [
        ('pending',  '未着手'),
        ('cooking',  '調理中'),
        ('served',   '提供済み'),
    ]
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='items', verbose_name='注文'
    )
    menu_item = models.ForeignKey(
        MenuItem, on_delete=models.PROTECT,
        verbose_name='メニュー'
    )
    quantity = models.PositiveIntegerField('数量', default=1)
    status = models.CharField('ステータス', max_length=10,
                              choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField('注文日時', auto_now_add=True)

    class Meta:
        verbose_name = '注文明細'
        verbose_name_plural = '注文明細'

    def __str__(self):
        return f'{self.menu_item.name} × {self.quantity}'

    def subtotal(self):
        return self.menu_item.price * self.quantity


# ──────────────────────────────────────────
# 農産物直売所向けモデル
# ──────────────────────────────────────────

class ProduceOrder(models.Model):
    """農産物直売所向け注文モデル"""
    STATUS_CHOICES = [
        ('pending',   '未確認'),
        ('confirmed', '確認済み・OK'),
        ('rejected',  'お断り'),
        ('shipped',   '発送済み'),
    ]
    ORDER_TYPE_CHOICES = [
        ('visit',    '来店受取'),
        ('delivery', '配送（贈答）'),
    ]
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE,
        related_name='produce_orders', verbose_name='店舗'
    )
    order_type = models.CharField(
        '注文種別', max_length=10,
        choices=ORDER_TYPE_CHOICES, default='visit'
    )
    # 申込者情報
    customer_name  = models.CharField('お名前', max_length=100)
    customer_phone = models.CharField('電話番号', max_length=20)
    customer_email = models.EmailField('メールアドレス', blank=True)
    # 来店
    visit_date     = models.DateField('来店予定日', null=True, blank=True)
    # 支払い
    payment_method = models.CharField('支払方法', max_length=10, default='cash')
    # 送り主情報（配送注文）
    sender_name        = models.CharField('送り主氏名', max_length=100, blank=True)
    sender_phone       = models.CharField('送り主電話番号', max_length=20, blank=True)
    sender_postal_code = models.CharField('送り主郵便番号', max_length=8, blank=True)
    sender_address     = models.TextField('送り主住所', blank=True)
    # 旧フィールド（後方互換のため残す）
    delivery_date  = models.DateField('希望配送日', null=True, blank=True)
    receiver_name  = models.CharField('届け先氏名', max_length=100, blank=True)
    receiver_phone = models.CharField('届け先電話番号', max_length=20, blank=True)
    postal_code    = models.CharField('郵便番号', max_length=8, blank=True)
    address        = models.TextField('住所', blank=True)
    # 決済
    stripe_payment_intent = models.CharField(
        'Stripe PaymentIntent ID', max_length=200, blank=True
    )
    is_paid = models.BooleanField('決済済み', default=False)
    # ステータス・備考
    status     = models.CharField('ステータス', max_length=10,
                                  choices=STATUS_CHOICES, default='pending')
    note       = models.TextField('備考', blank=True)
    created_at = models.DateTimeField('注文日時', auto_now_add=True)

    class Meta:
        verbose_name = '直売注文'
        verbose_name_plural = '直売注文'
        ordering = ['-created_at']

    def __str__(self):
        return f'直売注文#{self.pk}（{self.customer_name}）'

    def total_price(self):
        return sum(item.subtotal() for item in self.produce_items.all())


class DeliveryAddress(models.Model):
    """届け先（複数対応）・品種・箱サイズを届け先ごとに管理"""
    BOX_SIZE_CHOICES = [
        (1, '1kg箱'),
        (2, '2kg箱'),
        (5, '5kg箱'),
    ]
    order = models.ForeignKey(
        ProduceOrder, on_delete=models.CASCADE,
        related_name='delivery_addresses', verbose_name='注文'
    )
    index          = models.PositiveIntegerField('届け先番号', default=1)
    receiver_name  = models.CharField('届け先氏名', max_length=100)
    receiver_phone = models.CharField('届け先電話番号', max_length=20, blank=True)
    postal_code    = models.CharField('郵便番号', max_length=8, blank=True)
    address        = models.TextField('住所')
    delivery_date  = models.DateField('希望配送日', null=True, blank=True)
    box_size       = models.PositiveIntegerField('箱サイズ（kg）', choices=BOX_SIZE_CHOICES, default=2)
    box_count      = models.PositiveIntegerField('箱数', default=1)
    note           = models.TextField('個別備考（のし・比率など）', blank=True)

    class Meta:
        ordering = ['index']
        verbose_name = '届け先'
        verbose_name_plural = '届け先'

    def __str__(self):
        return f'#{self.order.pk} 届け先{self.index}：{self.receiver_name}'


class DeliveryAddressItem(models.Model):
    """届け先ごとの品種選択"""
    address = models.ForeignKey(
        DeliveryAddress, on_delete=models.CASCADE,
        related_name='items', verbose_name='届け先'
    )
    menu_item = models.ForeignKey(
        MenuItem, on_delete=models.PROTECT,
        verbose_name='品種'
    )

    class Meta:
        verbose_name = '品種選択'
        verbose_name_plural = '品種選択'

    def __str__(self):
        return f'{self.address} / {self.menu_item.name}'


class ProduceOrderItem(models.Model):
    """直売注文の明細（来店注文用）"""
    order = models.ForeignKey(
        ProduceOrder, on_delete=models.CASCADE,
        related_name='produce_items', verbose_name='注文'
    )
    menu_item = models.ForeignKey(
        MenuItem, on_delete=models.PROTECT,
        verbose_name='商品'
    )
    quantity = models.PositiveIntegerField('数量', default=1)

    class Meta:
        verbose_name = '直売注文明細'
        verbose_name_plural = '直売注文明細'

    def __str__(self):
        return f'{self.menu_item.name} × {self.quantity}'

    def subtotal(self):
        return self.menu_item.price * self.quantity
