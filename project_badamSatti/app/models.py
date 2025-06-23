# your_app_name/models.py
from django.db import models
import json

class Game(models.Model):
    """
    Represents a single Badam Satti game instance.
    Stores the entire state of the game.
    """
    game_id = models.CharField(max_length=50, unique=True, primary_key=True)
    # Stores the initial shuffled deck as a JSON string
    initial_deck_json = models.TextField()
    # Stores player hands as a JSON string
    # Example: {"1": [[1, "AH"], ...], "2": [[...]], ...}
    player_hands_json = models.TextField()
    # Stores the global desk state as a JSON string
    # Example: {"H": [[7, "7H"], ...], "D": [], ...}
    global_desk_json = models.TextField()
    current_player = models.IntegerField(default=1) # 1, 2, 3, or 4
    game_started = models.BooleanField(default=False)
    game_over = models.BooleanField(default=False)
    winner_player_num = models.IntegerField(null=True, blank=True)
    # Stores the mapping of card number to card string for quick lookup
    cards_map_json = models.TextField()
    # Track the player who has 7H, so they start first
    player_with_7h = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def set_initial_deck(self, deck):
        self.initial_deck_json = json.dumps(deck)

    def get_initial_deck(self):
        return json.loads(self.initial_deck_json)

    def set_player_hands(self, hands_dict):
        # Convert tuples (card_num, card_name) to lists for JSON serialization
        serializable_hands = {
            str(player_num): [[card[0], card[1]] for card in cards]
            for player_num, cards in hands_dict.items()
        }
        self.player_hands_json = json.dumps(serializable_hands)

    def get_player_hands(self):
        # Convert lists back to tuples if needed for game logic
        loaded_hands = json.loads(self.player_hands_json)
        # Ensure keys are integers if original was
        return {
            int(k): [[card[0], card[1]] for card in v]
            for k, v in loaded_hands.items()
        }

    def set_global_desk(self, desk_dict):
        # Convert tuples (card_num, card_name) to lists for JSON serialization
        serializable_desk = {
            suit: [[card[0], card[1]] for card in cards]
            for suit, cards in desk_dict.items()
        }
        self.global_desk_json = json.dumps(serializable_desk)

    def get_global_desk(self):
        # Convert lists back to tuples if needed for game logic
        loaded_desk = json.loads(self.global_desk_json)
        return {
            suit: [[card[0], card[1]] for card in cards_list]
            for suit, cards_list in loaded_desk.items()
        }

    def set_cards_map(self, cards_dict):
        # cards_dict is like {1: "AH", 2: "2H", ...}
        # It's already serializable as JSON, but we store it as a string key map
        self.cards_map_json = json.dumps({str(k): v for k, v in cards_dict.items()})

    def get_cards_map(self):
        loaded_map = json.loads(self.cards_map_json)
        # Convert keys back to integers for easy lookup
        return {int(k): v for k, v in loaded_map.items()}

    def __str__(self):
        return f"Game {self.game_id} - Current Player: {self.current_player}"

    class Meta:
        verbose_name = "Badam Satti Game"
        verbose_name_plural = "Badam Satti Games"