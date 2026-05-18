from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from orders.views import top

urlpatterns = [
    path('', top, name='top'),  # ← これを追加
    # 既存のパスはそのまま
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('reservations/', include('reservations.urls')),
    path('accounts/', include('accounts.urls')),
    path('orders/', include('orders.urls')),
    path('<str:store_slug>/', include('orders.store_urls')),
]
