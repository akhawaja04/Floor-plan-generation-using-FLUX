from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='imagegen-home'),
    path('main/', views.main, name='imagegen-main'),
    path('about/', views.about, name='imagegen-about'),
    path('generate_prompt/', views.generate_prompt, name='generate_prompt'),
    path('gallery/', views.gallery, name='gallery'),
    path('download_image/<str:format>/', views.download_image, name='download_image'),
    path('serve_image/<str:filename>/', views.serve_image, name='serve_image'),
]