from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from django.db.models import Q

from .models import CustomUser, VIA_EMAIL, VIA_PHONE, CodeVerify
from shared.utility import check_email_or_phone
from shared.utility import send_verification_email


class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    auth_status = serializers.CharField(read_only=True)
    auth_type = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email_or_phone'] = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'auth_status', 'auth_type']


    def validate(self, attrs):
        email_or_phone = self.initial_data.get('email_or_phone')
        if not email_or_phone:
            raise ValidationError({'email_or_phone': 'Bu maydon majburiy.'})

        already_exists = CustomUser.objects.filter(
            Q(phone_number=email_or_phone) | Q(email=email_or_phone)
        ).exists()
        if already_exists:
            raise ValidationError({'email_or_phone': 'Bu email yoki telefon bilan allaqachon ro\'yxatdan o\'tilgan.'})

        input_type = check_email_or_phone(email_or_phone)
        if input_type == 'phone':
            attrs['auth_type'] = VIA_PHONE
            attrs['phone_number'] = email_or_phone
        elif input_type == 'email':
            attrs['auth_type'] = VIA_EMAIL
            attrs['email'] = email_or_phone
        else:
            raise ValidationError({'email_or_phone': 'Email yoki telefon raqamingiz xato kiritilgan.'})


        attrs.pop('email_or_phone', None)
        return attrs


    def create(self, validated_data):
        user = super().create(validated_data)

        if user.auth_type == VIA_EMAIL:
            code = user.generate_code(VIA_EMAIL)
            send_verification_email(user.email, code)

        elif user.auth_type == VIA_PHONE:
            code = user.generate_code(VIA_PHONE)
        else:
            raise ValidationError('auth_type aniqlanmadi.')

        return user


    def to_representation(self, instance):
        data = super().to_representation(instance)
        tokens = instance.token()
        data['message'] = 'Tasdiqlash kodi yuborildi.'
        data['refresh'] = tokens['refresh']
        data['access'] = tokens['access']
        return data
