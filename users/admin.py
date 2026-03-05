from django.contrib import admin
from .models import CustomUser, CodeVerify

admin.site.register(CustomUser)
admin.site.register(CodeVerify)