from django.urls import path
from . import views

app_name = 'works'

urlpatterns = [
    # トップ画面（一覧画面）
    path('', views.ListView.as_view(), name='index'),

    # 詳細画面
    path('works/<int:pk>/', views.DetailView.as_view(), name='detail'),

    # 登録画面
    path('create/', views.CreateView.as_view(), name='create'),
]