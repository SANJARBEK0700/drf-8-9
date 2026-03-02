from django.db import models

# Create your models here.
from django.db import models

import uuid

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_add=True)
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)