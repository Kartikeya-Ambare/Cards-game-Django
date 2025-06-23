from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create_game/', views.create_game, name='create_game'),
    path('game_state/<str:game_id>/', views.get_game_state, name='get_game_state'),
    path('play_card/<str:game_id>/', views.play_card, name='play_card'),
]