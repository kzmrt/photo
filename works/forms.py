from .models import Work, Image
from django import forms
import os
from django_superform import ModelFormField, SuperModelForm

VALID_EXTENSIONS = ['.jpg']


class UploadFileForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('image',)

        image = forms.ImageField(
            label='画像',
            required=False,  # 必須 or 必須ではない
        )

    def clean_image(self):
        image = self.cleaned_data['image']
        if image:  # 画像ファイルが指定されている場合
            extension = os.path.splitext(image.name)[1]  # 拡張子を取得
            if not extension.lower() in VALID_EXTENSIONS:
                raise forms.ValidationError('jpgファイルを選択してください！')
        return image


class WorkSetForm(SuperModelForm):
    # 複数のフォームを使用する
    upload = ModelFormField(UploadFileForm)

    class Meta:
        model = Work
        fields = ('title', 'memo',)

        title = forms.CharField(
            initial='',
            label='タイトル',
            required=True,  # 必須
            max_length=255,
        )
        memo = forms.CharField(
            initial='',
            label='メモ',
            required=False,  # 必須ではない
            max_length=255,
        )
