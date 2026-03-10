from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from .models import CustomUser, CODE_VERIFY, DONE


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
    )

    password2 = serializers.CharField(write_only=True, label="Parolni tasdiqlang")

    class Meta:
        model = CustomUser
        fields = ["id", "username", "email", "password", "password2"]
        read_only_fields = ["id"]

    def validate(self, attrs):

        if attrs["password"] != attrs["password2"]:
            raise ValidationError({"password": "Parollar mos kelmadi."})

        return attrs

    def create(self, validated_data):

        validated_data.pop("password2")

        user = CustomUser.objects.create_user(**validated_data)

        return user


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ["id", "username", "email", "bio", "avatar", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class ChangePasswordSerializer(serializers.Serializer):

    old_password = serializers.CharField(write_only=True)

    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
    )

    new_password2 = serializers.CharField(write_only=True)

    def validate_old_password(self, value):

        user = self.context["request"].user

        if not user.check_password(value):
            raise ValidationError("Eski parol noto'g'ri.")

        return value

    def validate(self, attrs):

        if attrs["new_password"] != attrs["new_password2"]:
            raise ValidationError({"new_password": "Yangi parollar mos kelmadi."})

        return attrs

    def save(self, **kwargs):

        user = self.context["request"].user

        user.set_password(self.validated_data["new_password"])

        user.save()

        return user


class UserChangeInfoSerializer(serializers.ModelSerializer):

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    username = serializers.CharField(required=True)

    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "username",
            "password",
            "confirm_password",
        ]

    def validate(self, attrs):

        if attrs["password"] != attrs["confirm_password"]:
            raise ValidationError({"password": "Parollar mos kelmadi."})

        return attrs

    def validate_username(self, value):

        if CustomUser.objects.filter(username=value).exists():
            raise ValidationError("Bu username allaqachon mavjud.")

        return value

    def validate_first_name(self, value):

        if len(value) < 2:
            raise ValidationError("Ism juda qisqa.")

        return value

    def validate_last_name(self, value):

        if len(value) < 2:
            raise ValidationError("Familiya juda qisqa.")

        return value

    def update(self, instance, validated_data):

        if instance.auth_status != CODE_VERIFY:
            raise ValidationError(
                {"message": "Siz hali tasdiqlanmagansiz", "status": status.HTTP_400_BAD_REQUEST}
            )

        instance.first_name = validated_data.get("first_name")
        instance.last_name = validated_data.get("last_name")
        instance.username = validated_data.get("username")

        instance.set_password(validated_data.get("password"))

        instance.auth_status = DONE

        instance.save()

        return instance