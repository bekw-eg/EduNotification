from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import os
from django.utils.text import slugify 

def notification_image_path(instance, filename):
    """
    Суреттерді сақтау жолын құру
    Формат: notifications/{notification_id}/{filename}
    """
    if instance.id:
        # Егер notification сақталған болса, ID пайдалану
        folder_name = str(instance.id)
    else:
        # Егер notification әлі сақталмаған болса, уақыт белгісін пайдалану
        import time
        folder_name = f"temp_{int(time.time())}"
    
    # Файл атын қауіпсіз етіп өзгерту
    name, ext = os.path.splitext(filename)
    safe_name = slugify(name) + ext
    
    return os.path.join('notifications', folder_name, safe_name)

class Group(models.Model):
    name = models.CharField(max_length=100, verbose_name="Группа аты")
    description = models.TextField(blank=True, verbose_name="Сипаттама")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Құрылған уақыты")
    
    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группалар"
    
    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        """Группадағы мүшелер саны"""
        return self.customuser_set.count()

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Админ'),
        ('user', 'Пайдаланушы'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user', verbose_name="Роль")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, 
                              verbose_name="Группа", related_name='members')
    email = models.EmailField(unique=True, verbose_name="Электронды пошта")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Тіркелген уақыты")
    
    class Meta:
        verbose_name = "Пайдаланушы"
        verbose_name_plural = "Пайдаланушылар"
        ordering = ['-date_joined']
    
    def __str__(self):
        full_name = self.get_full_name()
        if full_name:
            return f"{full_name} ({self.get_role_display()})"
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def notifications_count(self):
        """Пайдаланушының жарияланған хабарландыруларының саны"""
        return self.notifications_created.count()
    
    @property
    def archived_notifications_count(self):
        """Пайдаланушының архивке қойған хабарландыруларының саны"""
        return self.notifications_archived.count()

class Notification(models.Model):
    TYPE_CHOICES = (
        ('general', 'Жалпы хабарландыру'),
        ('group', 'Группаға арналған хабарландыру'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Белсенді'),
        ('archived', 'Архивтелген'),
        ('deleted', 'Жойылған'),
    )
    
    title = models.CharField(max_length=200, verbose_name="Тақырып")
    content = models.TextField(verbose_name="Мазмұны")
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, 
                                        verbose_name="Түрі", default='general')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, 
                             verbose_name="Группа", related_name='notifications')
    

    image = models.ImageField(upload_to=notification_image_path, null=True, blank=True, 
                             verbose_name="Сурет")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', 
                             verbose_name="Статус")
    is_important = models.BooleanField(default=False, verbose_name="Маңызды")
    

    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, 
                                  verbose_name="Құрушы", related_name='notifications_created')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Құрылған уақыты")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Жаңартылған уақыты")
    

    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="Архивке қойған", 
                                   related_name='notifications_archived')
    archive_date = models.DateTimeField(null=True, blank=True, verbose_name="Архивтелген күні")
    archive_reason = models.TextField(blank=True, null=True, verbose_name="Архивтеу себебі")
    
    class Meta:
        verbose_name = "Хабарландыру"
        verbose_name_plural = "Хабарландырулар"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['notification_type', 'status']),
            models.Index(fields=['group', 'status']),
            models.Index(fields=['is_important', 'status']),
        ]
        permissions = [
            ("can_archive", "Хабарландыруды архивке қоюға болады"),
            ("can_restore", "Хабарландыруды архивтен қалпына келтіруге болады"),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.pk is None:
            super().save(*args, **kwargs)
            if self.image and hasattr(self.image, 'name'):
                self.image.name = notification_image_path(self, self.image.name)
                super().save(update_fields=['image'])
        else:
            super().save(*args, **kwargs)
    
    def archive(self, user=None, reason=''):
        """Хабарландыруды архивке ауыстыру"""
        self.status = 'archived'
        self.archived_by = user
        self.archive_date = timezone.now()
        self.archive_reason = reason
        self.save()

        NotificationArchive.objects.update_or_create(
            notification=self,
            defaults={
                'archived_by': user,
                'reason': reason
            }
        )
    
    def restore(self):
        """Хабарландыруды архивтен қалпына келтіру"""
        self.status = 'active'
        self.archived_by = None
        self.archive_date = None
        self.archive_reason = ''
        self.save()

        NotificationArchive.objects.filter(notification=self).delete()
    
    def soft_delete(self):
        """Хабарландыруды жұмсқа жою"""
        self.status = 'deleted'
        self.save()
    
    def can_archive(self, user):
        """Пайдаланушы хабарландыруды архивке қоя ала ма?"""
        if user.is_admin:
            return True
        
        if self.created_by == user:
            return True

        if self.notification_type == 'group' and self.group and user.group == self.group:
            return True
        
        return False
    
    def can_restore(self, user):
        """Пайдаланушы хабарландыруды қалпына келтіре ала ма?"""
        if user.is_admin:
            return True

        return self.archived_by == user
    
    def is_accessible_by(self, user):
        """Хабарландыру пайдаланушыға қолжетімді ме?"""
        if user.is_admin:
            return True
        
        if self.status == 'deleted':
            return False
        
        if self.status == 'archived':
            return self.archived_by == user
        
        if self.notification_type == 'general':
            return True
        
        if self.notification_type == 'group':
            return self.group and user.group == self.group
        
        return False
    
    def delete_image(self):
        """Хабарландыру суретін жою"""
        if self.image:
            if os.path.exists(self.image.path):
                try:
                    os.remove(self.image.path)
                except:
                    pass
            
            self.image.delete(save=True)
    
    @property
    def has_image(self):
        return bool(self.image)
    
    @property
    def is_archived(self):
        return self.status == 'archived'
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def short_content(self):
        """Қысқартылған мазмұн"""
        if len(self.content) > 150:
            return self.content[:147] + '...'
        return self.content
    
    @property
    def can_be_edited_by(self, user):
        """Пайдаланушы хабарландыруды өңдей ала ма?"""
        if user.is_admin:
            return True
        return self.created_by == user and self.status != 'deleted'
    
    @property
    def can_be_deleted_by(self, user):
        """Пайдаланушы хабарландыруды жоя ала ма?"""
        if user.is_admin:
            return True
        return self.created_by == user and self.status != 'deleted'

class NotificationArchive(models.Model):
    notification = models.OneToOneField(Notification, on_delete=models.CASCADE, 
                                        related_name='archive_record',
                                        verbose_name="Хабарландыру")
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True,
                                    related_name='archive_records',
                                    verbose_name="Архивке қойған")
    archived_at = models.DateTimeField(auto_now_add=True, verbose_name="Архивтелген уақыты")
    reason = models.TextField(blank=True, verbose_name="Архивтеу себебі")
    
    class Meta:
        verbose_name = "Архив жазбасы"
        verbose_name_plural = "Архив жазбалары"
        ordering = ['-archived_at']
    
    def __str__(self):
        return f"Архив: {self.notification.title}"
    
    @property
    def days_in_archive(self):
        """Архивте қанша күн болғаны"""
        if not self.archived_at:
            return 0
        delta = timezone.now() - self.archived_at
        return delta.days

class NotificationView(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, 
                            related_name='notification_views',
                            verbose_name="Пайдаланушы")
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE,
                                    related_name='views',
                                    verbose_name="Хабарландыру")
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="Қаралған уақыты")
    
    class Meta:
        verbose_name = "Қаралған хабарландыру"
        verbose_name_plural = "Қаралған хабарландырулар"
        unique_together = ['user', 'notification']
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.user} - {self.notification}"
    
    @classmethod
    def mark_as_viewed(cls, user, notification):
        """Хабарландыруды қаралған деп белгілеу"""
        cls.objects.update_or_create(
            user=user,
            notification=notification,
            defaults={'viewed_at': timezone.now()}
        )