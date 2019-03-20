from django.shortcuts import reverse
from django.views import generic
from .models import Work, Image
import logging
from photo import settings
import os
from django.contrib import messages
from django.http import HttpResponseRedirect
from .forms import WorkSetForm

logger = logging.getLogger('development')

NO_IMAGE = '/image/noimage.jpg'  # NO IMAGEパス


class ListView(generic.ListView):

    paginate_by = 5
    template_name = 'works/index.html'
    model = Work


class CreateView(generic.CreateView):
    # 登録画面
    model = Work
    form_class = WorkSetForm  # SuperModelFormをセットする。

    # def get_success_url(self):  # 詳細画面にリダイレクトする。
    #     return reverse('works:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):

        # result = super().form_valid(form)
        # return result

        # DBへの保存
        work = Work()
        work.title = form.instance.title
        work.memo = form.instance.memo
        work.save()

        if len(self.request.FILES) != 0 and\
                self.request.FILES['form-upload-image'].name:  # 画像ファイルが添付されている場合
            logger.debug("With Image.")

            # サーバーのアップロード先ディレクトリを作成、画像を保存
            save_dir = "/image/" + '{0}/'.format(work.pk)
            upload_dir = settings.MEDIA_ROOT + save_dir
            os.makedirs(upload_dir, exist_ok=True)  # ディレクトリが存在しない場合作成する
            path = os.path.join(upload_dir, self.request.FILES['form-upload-image'].name)
            with open(path, 'wb+') as destination:
                for chunk in self.request.FILES['form-upload-image'].chunks():
                    destination.write(chunk)

            # DBへの保存
            image = Image()
            image.work_id = work.pk  # 作品ID
            image.image = settings.MEDIA_URL + save_dir + self.request.FILES['form-upload-image'].name  # アップロードしたイメージパス（サーバー側）
            image.save()
        else:
            logger.debug("No Image.")

        messages.success(self.request, '作品情報を登録しました。')
        return HttpResponseRedirect(reverse('works:detail', kwargs={'pk': work.pk}))  # 詳細画面にリダイレクト

    def form_invalid(self, form):
        result = super().form_invalid(form)
        return result


class DetailView(generic.DetailView):
    # 詳細画面
    model = Work
    template_name = 'works/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if Image.objects.filter(work_id=self.object.pk).exists():  # 画像が紐づく場合
            # 作品に紐づく画像パスを取得
            image = Image.objects.values_list('image', flat=True).get(work_id=self.object.pk)
        else:
            # No Imageパス
            image = settings.MEDIA_URL + NO_IMAGE
        context['image'] = image

        return context
