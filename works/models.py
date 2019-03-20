from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser


class Work(models.Model):
    """作品モデル"""
    class Meta:
        db_table = 'work'

    title = models.CharField(verbose_name='タイトル', max_length=255)
    memo = models.CharField(verbose_name='メモ', max_length=255, default='', blank=True)
    created_at = models.DateTimeField(verbose_name='登録日時', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新日時', auto_now=True)

    def __str__(self):
        return self.title + self.memo

    @staticmethod
    def get_absolute_url(self):
        return reverse('works:index')


class Image(models.Model):
    """イメージモデル"""
    class Meta:
        db_table = 'image'

    work = models.ForeignKey(Work, verbose_name='作品', on_delete=models.CASCADE)
    image = models.ImageField(upload_to="image/", verbose_name='イメージ', null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='登録日時', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新日時', auto_now=True)

    def __str__(self):
        return self.work.title