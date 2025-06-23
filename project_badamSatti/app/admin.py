# your_app_name/admin.py
from django.contrib import admin
from .models import Game

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        'game_id', 'current_player', 'game_started',
        'game_over', 'winner_player_num', 'created_at', 'last_updated'
    )
    list_filter = ('game_started', 'game_over', 'current_player')
    search_fields = ('game_id',)
    readonly_fields = ('created_at', 'last_updated')
    fieldsets = (
        (None, {
            'fields': ('game_id', 'initial_deck_json', 'cards_map_json')
        }),
        ('Game State', {
            'fields': ('player_hands_json', 'global_desk_json', 'current_player', 'player_with_7h')
        }),
        ('Game Status', {
            'fields': ('game_started', 'game_over', 'winner_player_num')
        }),
    )