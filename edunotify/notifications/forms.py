from django import forms
from django.core.exceptions import ValidationError
from core.models import Notification
import os

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'content', 'notification_type', 'group', 'image', 'is_important']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Хабарландыру тақырыбы'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Хабарландыру мазмұны'
            }),
            'notification_type': forms.Select(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_important': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        
        if image:
            ext = os.path.splitext(image.name)[1].lower()[1:]
            if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                raise ValidationError('Тек JPG, JPEG, PNG, GIF, WebP форматтарындағы суреттерді жүктеуге болады.')
            
            if image.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError('Суреттің өлшемі 5MB-тан аспауы керек.')
        
        return image

class ArchiveForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Архивтеу себебі (міндетті емес)'
        }),
        required=False,
        label='Архивтеу себебі'
    )