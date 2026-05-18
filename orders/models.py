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
        ('confirmed', '確認済み'),
        ('shipped',   '発送済み'),
    ]
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE,
        related_name='produce_orders', verbose_name='店舗'
    )
    # 注文者情報
    customer_name  = models.CharField('お名前', max_length=100)
    customer_phone = models.CharField('電話番号', max_length=20)
    # 配送先
    postal_code = models.CharField('郵便番号', max_length=8)
    address     = models.TextField('住所')
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


class ProduceOrderItem(models.Model):
    """直売注文の明細"""
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
