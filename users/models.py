from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


VIA_EMAIL = "email"
VIA_PHONE = "phone"

EMAIL_EXPIRATION_TIME = 5
PHONE_EXPIRATION_TIME = 2


class CustomUser(AbstractUser):

    email = models.EmailField(unique=True)

    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name="Haqida"
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Rasm",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    recent_posts = models.ManyToManyField(
        "posts.Post",
        blank=True,
        related_name="recently_viewed_by",
        verbose_name="Oxirgi ko'rilgan postlar",
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.username

    def add_recent_post(self, post):

        from django.conf import settings

        max_count = getattr(settings, "MAX_RECENT_POSTS", 10)

        self.recent_posts.remove(post)
        self.recent_posts.add(post)

        ids = list(
            self.recent_posts.through.objects
            .filter(customuser_id=self.pk)
            .order_by("-id")
            .values_list("post_id", flat=True)
        )

        if len(ids) > max_count:
            old_ids = ids[max_count:]

            self.recent_posts.through.objects.filter(
                customuser_id=self.pk,
                post_id__in=old_ids,
            ).delete()


class BaseModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CodeVerify(BaseModel):

    VERIFY_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="verify_codes",
    )

    code = models.CharField(max_length=4)

    verify_type = models.CharField(
        choices=VERIFY_TYPE,
        max_length=30,
    )

    expiration_time = models.DateTimeField()

    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):

        if self.verify_type == VIA_EMAIL:
            self.expiration_time = timezone.now() + timedelta(
                minutes=EMAIL_EXPIRATION_TIME
            )
        else:
            self.expiration_time = timezone.now() + timedelta(
                minutes=PHONE_EXPIRATION_TIME
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.code