from django.core.management.base import BaseCommand
from accounts.models import Store

class Command(BaseCommand):
    def handle(self, *args, **options):
        if not Store.objects.filter(slug='itadaki').exists():
            Store.objects.create(name='阿波居酒屋 頂', slug='itadaki')
            self.stdout.write('Store created')
        else:
            self.stdout.write('Store already exists')
