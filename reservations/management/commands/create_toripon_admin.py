from django.core.management.base import BaseCommand
from accounts.models import Staff

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if not Staff.objects.filter(username='admin').exists():
            u = Staff(username='admin', is_staff=True, is_superuser=True, is_active=True)
            u.set_password('Toripon2026!')
            u.save()
            self.stdout.write('admin作成完了')
        else:
            self.stdout.write('adminは既に存在します')
