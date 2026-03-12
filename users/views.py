from datetime import datetime

from django.contrib.auth import authenticate
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser, NEW, CODE_VERIFY, DONE, PHONE_DONE, VIA_EMAIL, VIA_PHONE
from .serializers import RegisterSerializer, UserProfileSerializer, ChangePasswordSerializer



def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is not None:
        return Response(
            {
                "success": False,
                "status_code": response.status_code,
                "errors": response.data,
            },
            status=response.status_code,
        )

    return Response(
        {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "errors": {"detail": "Server xatosi yuz berdi."},
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )



def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}



class RegisterView(generics.CreateAPIView):

    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Muvaffaqiyatli ro'yxatdan o'tdingiz.",
                "user": UserProfileSerializer(user).data,
                **get_tokens(user),
            },
            status=status.HTTP_201_CREATED,
        )



class LoginView(APIView):

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["username", "password"],
            properties={
                "username": openapi.Schema(type=openapi.TYPE_STRING, example="ali_karimov"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, format="password", example="Test1234!"),
            },
        )
    )
    def post(self, request):

        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")

        if not username or not password:
            return Response(
                {"success": False, "message": "Username va parol kiritilishi shart."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {"success": False, "message": "Username yoki parol noto'g'ri."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {
                "success": True,
                "message": "Muvaffaqiyatli login.",
                "user": UserProfileSerializer(user).data,
                **get_tokens(user),
            },
            status=status.HTTP_200_OK,
        )



class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={"refresh": openapi.Schema(type=openapi.TYPE_STRING)},
        )
    )
    def post(self, request):

        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"success": False, "message": "Refresh token kiritilishi shart."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

        except TokenError:
            return Response(
                {"success": False, "message": "Token yaroqsiz yoki allaqachon bekor qilingan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"success": True, "message": "Muvaffaqiyatli chiqildi."},
            status=status.HTTP_200_OK,
        )



class ProfileView(generics.RetrieveUpdateAPIView):

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)



class ChangePasswordView(APIView):

    permission_classes = [IsAuthenticated]

    def put(self, request):

        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"success": True, "message": "Parol muvaffaqiyatli o'zgartirildi."},
            status=status.HTTP_200_OK,
        )



class CodeVerify(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        user = request.user
        code = request.data.get("code")

        codes = user.verify_codes.filter(
            code=code,
            expiration_time__gte=datetime.now(),
            is_expired=False,
        )

        if not codes.exists():
            raise ValidationError(
                {"message": "Kodingiz xato yoki eskirgan", "status": status.HTTP_400_BAD_REQUEST}
            )

        codes.update(is_active=True)

        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFY
            user.save()

        response_data = {
            "message": "Kod tasdiqlandi",
            "status": status.HTTP_200_OK,
            "access": user.token()["access"],
            "refresh": user.token()["refresh"],
        }

        return Response(response_data)



class GetNewCodeView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        user = request.user

        code = user.verify_codes.filter(
            expiration_time__gte=datetime.now(),
            is_active=False,
        )

        if code.exists():
            raise ValidationError(
                {"message": "Sizda hali active kod bor", "status": status.HTTP_400_BAD_REQUEST}
            )

        if user.auth_type == VIA_EMAIL:
            user.generate_code(VIA_EMAIL)

        elif user.auth_type == VIA_PHONE:
            user.generate_code(VIA_PHONE)

        response_data = {
            "message": "Yangi kod yuborildi",
            "status": status.HTTP_201_CREATED,
        }

        return Response(response_data)