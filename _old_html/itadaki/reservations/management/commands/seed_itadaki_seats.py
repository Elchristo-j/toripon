"""
reservations/management/commands/seed_itadaki_seats.py
=======================================================
頂（いただき）の初期席データを投入するコマンド。

使い方:
  python manage.py seed_itadaki_seats

前提:
  - accounts.Store に store_code="itadaki" のレコードが存在すること
  - reservations の migrate 完了済みであること
"""

from django.core.management.base import BaseCommand
from accounts.models import Store
from reservations.models import Seat, SeatLink, SeatSection


SECTIONS = [
    # (name, section_type, sort_order, seats)
    # seats: (code, capacity, can_merge, sort_order)
    (
        "カウンター", "counter", 1,
        [
            ("C-1", 1, False, 1),
            ("C-2", 1, False, 2),
            ("C-3", 1, False, 3),
            ("C-4", 1, False, 4),
            ("C-5", 1, False, 5),
            ("C-6", 1, False, 6),
        ],
    ),
    (
        "テーブル", "table", 2,
        [
            ("T-1", 4, False, 1),
            ("T-2", 4, False, 2),
            ("T-3", 4, False, 3),
        ],
    ),
    (
        "掘り炬燵", "kotatsu", 3,
        [
            ("K-1", 5, True, 1),
            ("K-2", 5, True, 2),
            ("K-3", 5, True, 3),
            ("K-4", 5, True, 4),
        ],
    ),
]

# 掘り炬燵の隣接関係（連結可能な組み合わせ）
KOTATSU_LINKS = [
    ("K-1", "K-2"),
    ("K-2", "K-3"),
    ("K-3", "K-4"),
]


class Command(BaseCommand):
    help = "頂（いただき）の席マスタを初期投入する"

    def handle(self, *args, **options):
        try:
            store = Store.objects.get(slug="itadaki")
        except Store.DoesNotExist:
            self.stderr.write(
                "store_code='itadaki' の Store が見つかりません。\n"
                "先に管理画面で Store を作成してください。"
            )
            return

        seat_map: dict[str, Seat] = {}

        for section_name, section_type, sort_order, seats_data in SECTIONS:
            section, created = SeatSection.objects.get_or_create(
                store=store,
                name=section_name,
                defaults={
                    "section_type": section_type,
                    "sort_order": sort_order,
                },
            )
            action = "作成" if created else "更新スキップ"
            self.stdout.write(f"  SeatSection [{action}]: {section_name}")

            for code, capacity, can_merge, seat_order in seats_data:
                seat, created = Seat.objects.get_or_create(
                    section=section,
                    code=code,
                    defaults={
                        "capacity": capacity,
                        "can_merge": can_merge,
                        "sort_order": seat_order,
                    },
                )
                seat_map[code] = seat
                action = "作成" if created else "スキップ"
                self.stdout.write(f"    Seat [{action}]: {code}（定員{capacity}）")

        self.stdout.write("\n掘り炬燵の連結設定...")
        for code_a, code_b in KOTATSU_LINKS:
            seat_a = seat_map.get(code_a)
            seat_b = seat_map.get(code_b)
            if seat_a and seat_b:
                link, created = SeatLink.objects.get_or_create(
                    seat_a=seat_a, seat_b=seat_b
                )
                action = "作成" if created else "スキップ"
                self.stdout.write(f"  SeatLink [{action}]: {code_a} ↔ {code_b}")

        self.stdout.write(self.style.SUCCESS("\n✅ 席マスタの初期投入が完了しました"))
        self.stdout.write(
            f"  カウンター: 6席 / テーブル: 3卓 / 掘り炬燵: 4ブロック\n"
            f"  合計 {Seat.objects.filter(section__store=store).count()} 席"
        )
