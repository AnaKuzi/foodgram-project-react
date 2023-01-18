import base64
from datetime import datetime

from django.core.files.base import ContentFile
from foodgram.settings import DATE_DISPLAY
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Переопределение кодировки изображений."""
    def to_internal_value(self, data):
        format, imgstr = data.split(';base64,')
        ext = format.split('/')[-1]
        name = (
            datetime.now().strftime(DATE_DISPLAY)
            + '_recipe_image.'
            + ext
        )
        result = ContentFile(base64.b64decode(imgstr), name=name)
        return super(Base64ImageField, self).to_internal_value(result)
