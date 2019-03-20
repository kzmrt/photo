from django.shortcuts import reverse
from django.views import generic
from .models import Work, Image
import logging
from photo import settings
import os
from django.contrib import messages
from django.http import HttpResponseRedirect
from .forms import WorkSetForm
from reportlab.pdfgen import canvas
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import portrait
from reportlab.lib.units import mm
from reportlab.platypus import Table
from reportlab.platypus import TableStyle
from reportlab.lib import colors
from django.http import HttpResponse

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


class BasicPdf(generic.View):
    filename = 'photo_work.pdf'  # 出力ファイル名
    title = 'title: Photo Works'
    font_name = 'HeiseiKakuGo-W5'  # フォント
    is_bottomup = True

    def get(self, request, *args, **kwargs):

        # PDF出力
        response = HttpResponse(status=200, content_type='application/pdf')
        # response['Content-Disposition'] = 'attachment; filename="{}"'.format(self.filename)  # ダウンロードする場合
        response['Content-Disposition'] = 'filename="{}"'.format(self.filename)  # 画面に表示する場合

        # A4縦書きのpdfを作る
        size = portrait(A4)

        # pdfを描く場所を作成：位置を決める原点は左上にする(bottomup)
        # デフォルトの原点は左下
        p = canvas.Canvas(response, pagesize=size, bottomup=self.is_bottomup)

        pdfmetrics.registerFont(UnicodeCIDFont(self.font_name))
        p.setFont(self.font_name, 16)  # フォントを設定

        # pdfのタイトルを設定
        p.setTitle(self.title)

        # 全ての作品情報を出力する。（検索結果は無関係）
        id_array = list(Work.objects.all().values_list('pk', flat=True))

        for work_count, work_id in enumerate(id_array):

            logger.debug(work_count)

            if Image.objects.filter(work_id=work_id).exists():  # 画像が紐づく場合
                # 作品に紐づく画像パスを取得
                image = Image.objects.values_list('image', flat=True).get(work_id=work_id)
            else:
                # No Imageパス
                image = settings.MEDIA_URL + NO_IMAGE

            # 作品情報
            workInfo = Work.objects.filter(pk=work_id).first()

            # 表の情報
            data = [
                ['タイトル', workInfo.title, 'メモ', workInfo.memo],
            ]

            table = Table(data, (15 * mm, 50 * mm, 12 * mm, 50 * mm), None, hAlign='CENTER')
            # TableStyleを使って、Tableの装飾をします。
            table.setStyle(TableStyle([
                # 表で使うフォントとそのサイズを設定
                ('FONT', (0, 0), (-1, -1), self.font_name, 9),
                # 四角に罫線を引いて、0.5の太さで、色は黒
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                # 四角の内側に格子状の罫線を引いて、0.25の太さで、色は黒
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                # セルの縦文字位置
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.darkblue),
                ('TEXTCOLOR', (2, 0), (2, 0), colors.darkblue),
            ]))

            if work_count % 2 == 0:  # 偶数の場合

                # 画像の描画
                p.drawImage(ImageReader(image[1:]), 10, 530, width=580, height=280, mask='auto',
                            preserveAspectRatio=True)

                # tableを描き出す位置を指定
                table.wrapOn(p, 50 * mm, 50 * mm)
                table.drawOn(p, 43 * mm, 160 * mm)

            else:  # 奇数の場合

                # 画像の描画
                p.drawImage(ImageReader(image[1:]), 10, 130, width=580, height=280, mask='auto',
                            preserveAspectRatio=True)

                # tableを描き出す位置を指定
                table.wrapOn(p, 50 * mm, 50 * mm)
                table.drawOn(p, 43 * mm, 19 * mm)

                p.showPage()  # Canvasに書き込み（改ページ）

        if len(id_array) % 2 != 0:  # 出力作品数が奇数の場合
            p.showPage()  # Canvasに書き込み
        p.save()  # ファイル保存

        self._draw(p)

        return response

    def _draw(self, p):
        pass