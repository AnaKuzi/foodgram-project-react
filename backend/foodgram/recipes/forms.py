from django.forms import ModelForm
from django.forms.widgets import TextInput

from .models import Tag


class TagModelForm(ModelForm):
    """Форма для добавления тэга"""
    class Meta:
        model = Tag
        fields = '__all__'
        widgets = {
            "color": TextInput(attrs={"type": "color"}),
        }
