import re
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings

email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
phone_regex = re.compile(r'^998([378]{2}|(9[013-57-9]))\d{7}$')


def check_email_or_phone(user_input):
    if re.fullmatch(phone_regex, user_input):
        return 'phone'
    elif re.fullmatch(email_regex, user_input):
        return 'email'
    else:
        response = {
            'status': status.HTTP_400_BAD_REQUEST,
            'message': "email yoki telefon raqamingiz xato kiritilgan"
        }
        raise ValidationError(response)




def send_verification_email(email: str, code: int):
    subject = "Email tasdiqlash kodi"
    message = (
        f"Assalomu alaykum!\n\n"
        f"Ro'yxatdan o'tish uchun tasdiqlash kodingiz: {code}\n\n"
        f"Kod {settings.EMAIL_EXPIRATION_TIME} daqiqa davomida amal qiladi.\n\n"
        f"Agar siz ro'yxatdan o'tmagan bo'lsangiz, ushbu xabarni e'tiborsiz qoldiring."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )