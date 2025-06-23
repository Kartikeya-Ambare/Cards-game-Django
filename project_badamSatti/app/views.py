import random
import json
import uuid # For generating unique game IDs

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse

from .models import Game # Your new Game model

# --- Your original game logic functions (adapted for Django context) ---
# It's better to refactor these into a separate utility file (e.g., game_logic.py)
# and import them, but for this example, they're here.

# Defining the cards (Moved here from global scope of the badam_satti.py)
CARDS_MAP = {
    1:"AH", 2:"2H", 3:"3H", 4:"4H", 5:"5H", 6:"6H", 7:"7H", 8:"8H", 9:"9H", 10:"TH", 11:"JH", 12:"QH", 13:"KH",
    14:"AD", 15:"2D", 16:"3D", 17:"4D", 18:"5D", 19:"6D", 20:"7D", 21:"8D", 22:"9D", 23:"TD", 24:"JD", 25:"QD", 26:"KD",
    27:"AC", 28:"2C", 29:"3C", 30:"4C", 31:"5C", 32:"6C", 33:"7C", 34:"8C", 35:"9C", 36:"TC", 37:"JC", 38:"QC", 39:"KC",
    40:"AS", 41:"2S", 42:"3S", 43:"4S", 44:"5S", 45:"6S", 46:"7S", 47:"8S", 48:"9S", 49:"TS", 50:"JS", 51:"QS", 52:"KS",
}

def create_shuffled_deck():
    deck = [(num, card_str) for num, card_str in CARDS_MAP.items()]
    random.shuffle(deck)
    print("DEBUG: Shuffled deck created.")
    return deck

def get_cards_distributed(shuffled_deck):
    players_hands = {1: [], 2: [], 3: [], 4: []}
    current_deck = list(shuffled_deck) # Make a mutable copy
    for i in range(1, 5):
        for _ in range(13):
            if current_deck:
                curr_card = current_deck.pop(0)
                players_hands[i].append(curr_card)
    print(f"DEBUG: Cards distributed. Player hands: {players_hands}")
    return players_hands

def get_card_value(card):
    # card can be a tuple (num, card_str) or just card_str
    card_string = card[1] if isinstance(card, (tuple, list)) else card
    
    # Handle values correctly: 'A' for Ace (1), 'T' for 10, 'J' for Jack (11), etc.
    if card_string[0] == 'A': return 1
    elif card_string[0] == 'T': return 10
    elif card_string[0] == 'J': return 11
    elif card_string[0] == 'Q': return 12
    elif card_string[0] == 'K': return 13
    else: return int(card_string[0]) # For '2' through '9'

def get_card_suit(card):
    # card can be a tuple (num, card_str) or just card_str
    card_string = card[1] if isinstance(card, (tuple, list)) else card
    return card_string[-1] # Last character is the suit

def is_valid_move(card, global_desk):
    # card is expected to be a tuple/list (card_number, card_string)
    card_number, card_string = card
    suit = get_card_suit(card_string)
    value = get_card_value(card_string)
    
    print(f"DEBUG: is_valid_move called for card: {card_string}, Suit: {suit}, Value: {value}")
    print(f"DEBUG: Current global desk for validity check: {global_desk}")
    
    is_first_move_of_game = True
    for s in global_desk:
        if global_desk[s]: # If any suit has cards, it's not the first move
            is_first_move_of_game = False
            break

    if is_first_move_of_game:
        print(f"DEBUG: First move of game. Card is 7H? {card_string == '7H'}")
        return card_string == "7H"
    
    # Check if this suit hasn't been started, only 7 of that suit can be played
    if not global_desk[suit]: # len(global_desk[suit]) == 0
        print(f"DEBUG: Suit {suit} not started. Card is 7 of {suit}? {value == 7}")
        return value == 7
    
    # If suit has been started, check if card is consecutive
    suit_cards = global_desk[suit]
    # Ensure suit_cards contain tuples/lists (number, card_string)
    played_values = [get_card_value(c) for c in suit_cards]
    
    # Check if there are played cards for this suit to find min/max
    if not played_values: # This case should be caught by the `not global_desk[suit]` above, but as a safeguard
        print(f"DEBUG: Fallback: Suit {suit} has no played cards. Card is 7 of {suit}? {value == 7}")
        return value == 7 # Can only play 7 to start a suit

    min_val = min(played_values)
    max_val = max(played_values)
    
    # Card can be played if it's one higher or one lower than existing range
    valid = (value == min_val - 1) or (value == max_val + 1)
    print(f"DEBUG: Suit {suit} already started. Card value {value}. Min played: {min_val}, Max played: {max_val}. Valid? {valid}")
    return valid

def get_valid_cards_for_player(player_cards, global_desk):
    valid_cards = []
    print(f"DEBUG: Getting valid cards for player. Player cards: {player_cards}")
    for card in player_cards:
        # Convert list to tuple for consistency
        card_tuple = tuple(card) if isinstance(card, list) else card
        if is_valid_move(card_tuple, global_desk):
            valid_cards.append(card_tuple)
    print(f"DEBUG: Valid cards found: {valid_cards}")
    return valid_cards

def find_player_with_7h(players_hands):
    print("DEBUG: Searching for player with 7H...")
    for player_num, cards in players_hands.items():
        # Check both tuple and list formats
        for card in cards:
            card_tuple = tuple(card) if isinstance(card, list) else card
            if card_tuple == (7, "7H"):
                print(f"DEBUG: Player {player_num} has 7H.")
                return player_num
    print("DEBUG: 7H not found in any player hand.")
    return None # Should not happen in a valid game distribution

def convert_hands_to_tuples(player_hands):
    """Convert player hands from lists to tuples for game logic consistency"""
    return {
        player_num: [tuple(card) if isinstance(card, list) else card for card in cards]
        for player_num, cards in player_hands.items()
    }

def convert_desk_to_tuples(global_desk):
    """Convert global desk from lists to tuples for game logic consistency"""
    return {
        suit: [tuple(card) if isinstance(card, list) else card for card in cards]
        for suit, cards in global_desk.items()
    }

# --- Django Views ---

def index(request):
    """
    Renders the initial game page.
    """
    return render(request, 'intoBadam_game.html')

def create_game(request):
    """
    API endpoint to create a new Badam Satti game.
    """
    if request.method == 'POST':
        game_id = str(uuid.uuid4()) # Generate a unique game ID
        
        # 1. Create a shuffled deck
        shuffled_deck = create_shuffled_deck()
        
        # 2. Distribute cards to players
        players_hands = get_cards_distributed(shuffled_deck)
        
        # 3. Find who has 7H to determine the starting player
        player_with_7h = find_player_with_7h(players_hands)
        if player_with_7h is None:
            print("ERROR: Could not find 7H after distribution. Game creation aborted.")
            return JsonResponse({'status': 'error', 'message': 'Could not find 7H in any player hand. Game creation failed.'}, status=500)

        # 4. Initialize global desk
        initial_global_desk = {"H": [], "D": [], "C": [], "S": []}

        # 5. Create the Game model instance
        game = Game( # Use Game(...) then set, then save for TextField properties
            game_id=game_id,
            current_player=player_with_7h, # Game starts with the player having 7H
            game_started=True,
            player_with_7h=player_with_7h
        )
        game.set_initial_deck(shuffled_deck) # Use setter
        game.set_player_hands(players_hands) # Use setter
        game.set_global_desk(initial_global_desk) # Use setter
        game.set_cards_map(CARDS_MAP) # Use setter
        game.save() # Save the JSON fields

        print(f"DEBUG: Game {game.game_id} created successfully. Starting player: {game.current_player}")
        return JsonResponse({'status': 'success', 'game_id': game.game_id, 'message': 'Game created successfully.', 'player_with_7h': game.player_with_7h})
    
    print("ERROR: create_game received non-POST request.")
    return HttpResponseBadRequest("Only POST requests are allowed for game creation.")

def get_game_state(request, game_id):
    """
    API endpoint to retrieve the current state of a game.
    """
    print(f"DEBUG: Fetching game state for game_id: {game_id}")
    game = get_object_or_404(Game, game_id=game_id)
    
    player_hands = game.get_player_hands()
    global_desk = game.get_global_desk()
    cards_map = game.get_cards_map() # Ensure cards_map is available

    # Convert to tuples for game logic
    player_hands_tuples = convert_hands_to_tuples(player_hands)
    global_desk_tuples = convert_desk_to_tuples(global_desk)

    # Determine valid cards for the current player
    current_player_hand = player_hands_tuples.get(game.current_player, [])
    valid_cards_tuples = get_valid_cards_for_player(current_player_hand, global_desk_tuples)
    
    # Format valid_cards for JSON response (num and string)
    valid_moves_for_current_player = [
        {'card_num': c[0], 'card_name': c[1]} for c in valid_cards_tuples
    ]

    # Format global desk for display (suit: [card_strings])
    formatted_desk = {}
    for suit, cards in global_desk.items():
        # Convert to tuples for sorting
        cards_tuples = [tuple(card) if isinstance(card, list) else card for card in cards]
        sorted_cards = sorted(cards_tuples, key=lambda x: get_card_value(x))
        formatted_desk[suit] = [card[1] for card in sorted_cards]

    response_data = {
        'game_id': game.game_id,
        'current_player': game.current_player,
        'game_started': game.game_started,
        'game_over': game.game_over,
        'winner_player_num': game.winner_player_num,
        'player_hands': {
            str(p_num): [card[1] if isinstance(card, list) else card[1] for card in hand] # Send only card strings for display, keys as strings
            for p_num, hand in player_hands.items()
        },
        'global_desk': formatted_desk,
        'valid_moves_for_current_player': valid_moves_for_current_player,
        'num_cards_per_player': {
            str(p_num): len(hand) for p_num, hand in player_hands.items() # Keys as strings
        },
        'player_with_7h': game.player_with_7h,
        'cards_map': cards_map # Include cards_map for frontend lookup
    }
    print(f"DEBUG: Sending game state for {game_id}. Current player: {game.current_player}. Valid moves: {valid_moves_for_current_player}")
    return JsonResponse(response_data)


def play_card(request, game_id):
    """
    API endpoint for a player to make a move.
    Receives card_num from the AJAX request.
    """
    if request.method == 'POST':
        print(f"DEBUG: Play card request for game_id: {game_id}")
        game = get_object_or_404(Game, game_id=game_id)

        if game.game_over:
            print("ERROR: Game is already over.")
            return JsonResponse({'status': 'error', 'message': 'Game is already over.'}, status=400)

        try:
            data = json.loads(request.body)
            card_number = int(data.get('card_num'))
            print(f"DEBUG: Received card_num: {card_number} from request.")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"ERROR: Invalid card number or request format: {e}")
            return JsonResponse({'status': 'error', 'message': 'Invalid card number or request format.'}, status=400)

        player_hands = game.get_player_hands()
        global_desk = game.get_global_desk()
        cards_map = game.get_cards_map()

        # Convert to tuples for game logic
        player_hands_tuples = convert_hands_to_tuples(player_hands)
        global_desk_tuples = convert_desk_to_tuples(global_desk)

        current_player = game.current_player
        player_current_hand = player_hands_tuples.get(current_player, [])
        print(f"DEBUG: Player {current_player}'s current hand: {player_current_hand}")

        # Find the selected card tuple from the player's hand
        selected_card = None
        for card_tuple in player_current_hand:
            if card_tuple[0] == card_number:
                selected_card = card_tuple
                break
        
        if not selected_card:
            print(f"ERROR: Card {card_number} not found in Player {current_player}'s hand.")
            return JsonResponse({'status': 'error', 'message': f"Card {card_number} not found in Player {current_player}'s hand."}, status=400)

        # Validate the move
        if not is_valid_move(selected_card, global_desk_tuples):
            print(f"ERROR: Card {selected_card[1]} is not a valid move for Player {current_player}.")
            return JsonResponse({'status': 'error', 'message': f"Card {selected_card[1]} is not a valid move for Player {current_player}."}, status=400)

        # --- Execute the move ---
        player_current_hand.remove(selected_card) # Remove from player's hand
        suit = get_card_suit(selected_card[1]) # Pass the string part to get_card_suit
        global_desk_tuples[suit].append(selected_card) # Add to global desk

        # Convert back to lists for storage
        player_hands_lists = {
            player_num: [list(card) for card in cards]
            for player_num, cards in player_hands_tuples.items()
        }
        global_desk_lists = {
            suit: [list(card) for card in cards]
            for suit, cards in global_desk_tuples.items()
        }

        # Update model's JSON fields
        game.set_player_hands(player_hands_lists)
        game.set_global_desk(global_desk_lists)
        print(f"DEBUG: Player {current_player} played {selected_card[1]}. Hand updated, Desk updated.")

        # Check for win condition
        if not player_current_hand: # Current player has no cards left
            game.game_over = True
            game.winner_player_num = current_player
            game.save()
            print(f"DEBUG: Player {current_player} wins the game!")
            return JsonResponse({
                'status': 'success',
                'message': f"Player {current_player} played {selected_card[1]} and wins the game!",
                'game_over': True,
                'winner_player_num': current_player
            })
        
        # Move to next player
        next_player = (current_player % 4) + 1
        print(f"DEBUG: Next player in sequence: {next_player}")
        
        # Logic for skipping players who are stuck
        checked_players = set()
        can_continue = False
        original_next_player = next_player
        
        while len(checked_players) < 4:
            checked_players.add(next_player)
            next_player_hand = player_hands_tuples.get(next_player, [])
            valid_cards_for_next = get_valid_cards_for_player(next_player_hand, global_desk_tuples)
            print(f"DEBUG: Checking Player {next_player}. Hand: {next_player_hand}, Valid moves: {valid_cards_for_next}")

            if next_player_hand and valid_cards_for_next:
                # Found a player with cards and valid moves
                game.current_player = next_player
                can_continue = True
                print(f"DEBUG: Found next active player: {game.current_player}")
                break
            elif not next_player_hand: # Player has no cards, they're out
                print(f"DEBUG: Player {next_player} has no cards, skipping turn.")
            else: # Player has cards but no valid moves
                print(f"DEBUG: Player {next_player} has cards but no valid moves, skipping turn.")

            next_player = (next_player % 4) + 1 # Go to the absolute next player in sequence

        if not can_continue: # All players checked and none can move
            # Check if any player still has cards
            players_with_cards = [p for p, cards in player_hands_tuples.items() if cards]
            if players_with_cards:
                # Find player with fewest cards as winner
                winner = min(players_with_cards, key=lambda p: len(player_hands_tuples[p]))
                game.game_over = True
                game.winner_player_num = winner
                game.save()
                print(f"DEBUG: All players are stuck! Player {winner} wins with fewest cards.")
                return JsonResponse({
                    'status': 'success',
                    'message': f"All players are stuck! Player {winner} wins with the fewest cards.",
                    'game_over': True,
                    'winner_player_num': winner
                })
            else:
                # This shouldn't happen, but handle it
                game.game_over = True
                game.winner_player_num = None # Draw
                game.save()
                print("DEBUG: All players are out of cards! Game ends in a draw.")
                return JsonResponse({
                    'status': 'success',
                    'message': "All players are out of cards! Game ends in a draw.",
                    'game_over': True,
                    'winner_player_num': None
                })
        
        game.save() # Save the updated game state

        print(f"DEBUG: Move successful. Current player: {game.current_player}")
        return JsonResponse({
            'status': 'success',
            'message': f"Player {current_player} played {selected_card[1]}. It's now Player {game.current_player}'s turn.",
            'game_over': False,
            'current_player': game.current_player, # Send back the new current player
        })

    print("ERROR: play_card received non-POST request.")
    return HttpResponseBadRequest("Only POST requests are allowed for playing a card.")