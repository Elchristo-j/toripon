from django import forms
from .models import Reservation, Seat


class ReservationForm(forms.ModelForm):
    seats = forms.ModelMultipleChoiceField(
        queryset=Seat.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        label="席を選ぶ",
    )
    class Meta:
        model = Reservation
        fields = ['guest_name', 'guest_phone', 'party_size', 'start_at', 'end_at', 'channel', 'notes']
        labels = {
            'guest_name': 'お名前',
            'guest_phone': '電話番号',
            'party_size': '人数',
            'start_at': '来店日時',
            'end_at': '退席予定日時',
            'channel': '予約経路',
            'notes': '備考',
        }
        widgets = {
            'start_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_at':   forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class StaffReservationForm(forms.Form):
    CHANNEL_CHOICES = [
        ('phone',     'TEL'),
        ('hotpepper', 'HPB'),
        ('tabelog',   'TBG'),
        ('gate',      'GATE'),
        ('walk',      'WALK-IN'),
        ('web',       'WEB'),
        ('staff',     'STAFF'),
    ]
    COURSE_CHOICES = [
        ('',        'SEAT ONLY'),
        ('drink',   'DRINK 2H'),
        ('okinari', 'OKINARI 8'),
        ('awa',     'AWA 8'),
        ('itadaki', 'ITADAKI 9'),
    ]

    channel = forms.ChoiceField(
        label='予約経路', choices=CHANNEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    visit_date = forms.DateField(
        label='来店日',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d'],
    )
    visit_time = forms.TimeField(
        label='来店時間', initial='18:00',
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}, format='%H:%M'),
        input_formats=['%H:%M'],
    )
    party_size = forms.IntegerField(
        label='人数', min_value=1, max_value=30,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    course = forms.ChoiceField(
        label='コース', choices=COURSE_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    seats = forms.ModelMultipleChoiceField(
        label='席', queryset=Seat.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple(),
    )
    guest_name = forms.CharField(
        label='お名前', max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    guest_phone = forms.CharField(
        label='電話番号', max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    guest_email = forms.EmailField(
        label='メール', required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    notes = forms.CharField(
        label='備考', required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )
    staff_memo = forms.CharField(
        label='スタッフメモ', required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
    )

    def clean(self):
        from django.utils import timezone
        cleaned = super().clean()
        visit_date = cleaned.get('visit_date')
        if visit_date and visit_date.weekday() == 0:
            self.add_error('visit_date', '月曜日は定休日です。')
        if visit_date and visit_date < timezone.localdate():
            self.add_error('visit_date', '過去の日付は登録できません。')
        return cleaned
