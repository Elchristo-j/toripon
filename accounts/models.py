from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser


class Store(models.Model):
    """店舗モデル（1レコード＝1店舗）"""
    name = models.CharField(max_length=100, verbose_name='店舗名')
    slug = models.SlugField(unique=True, verbose_name='スラッグ')
    phone = models.CharField(max_length=20, blank=True, verbose_name='電話番号')
    address = models.TextField(blank=True, verbose_name='住所')
    area = models.CharField(max_length=50, blank=True, verbose_name='エリア（例：徳島市）')
    genre = models.CharField(max_length=50, blank=True, verbose_name='ジャンル（例：居酒屋）')
    business_hours = models.CharField(max_length=100, blank=True, verbose_name='営業時間（例：17:00〜24:00）')
    closed_day = models.CharField(max_length=100, blank=True, verbose_name='定休日（例：月曜日）')
    theme_color = models.CharField(max_length=7, default='#2d6a4f', verbose_name='イメージカラー（例：#c9a84c）')
    theme_text_color = models.CharField(max_length=7, default='#ffffff', verbose_name='テキストカラー（例：#c9a84c）')
    reservation_url = models.URLField(blank=True, verbose_name='予約URL')
    is_active = models.BooleanField(default=True, verbose_name='有効')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '店舗'
        verbose_name_plural = '店舗一覧'

    def __str__(self):
        return self.name


class Staff(AbstractUser):
    """スタッフモデル（Djangoの認証ユーザーを拡張）"""
    class Role(models.TextChoices):
        STAFF = 'staff', 'スタッフ'
        MANAGER = 'manager', '店長'
        OWNER = 'owner', 'オーナー'
        CHIEF_ADMINISTRATOR = 'chief_administrator', '最高管理者'
        ADMINISTRATOR = 'administrator', '管理人'
        
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='staffs',
        verbose_name='所属店舗'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STAFF,
        verbose_name='役割'
    )

    class Meta:
        verbose_name = 'スタッフ'
        verbose_name_plural = 'スタッフ一覧'

    def __str__(self):
        return f'{self.store} / {self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_manager(self):
        return self.role in [self.Role.OWNER, self.Role.MANAGER]
