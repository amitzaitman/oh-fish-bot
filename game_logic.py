import random
import os
from dotenv import load_dotenv

load_dotenv()
NUM_PLAYERS = int(os.environ.get('NUM_PLAYERS', 2))
class Card:
    SUITS = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}
    RANKS = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    @classmethod
    def from_string(cls, card_string):
        if len(card_string) == 2:
            return cls(card_string[0], card_string[1])
        elif len(card_string) == 3:
            return cls(card_string[:2], card_string[2])
        else:
            raise ValueError(f"Invalid card string: {card_string}")

    def __str__(self):
        return f"{self.rank}{self.SUITS.get(self.suit, self.suit)}"

    def __repr__(self):
        return self.__str__()

class Deck:
    def __init__(self):
        self.cards = [Card(rank, suit) for suit in Card.SUITS.keys() for rank in Card.RANKS]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop() if self.cards else None

class Crypto:
    @staticmethod
    def encrypt(text, key):
        return ''.join(chr((ord(c) + key) % 128) for c in text)

    @staticmethod
    def decrypt(text, key):
        return ''.join(chr((ord(c) - key) % 128) for c in text)

class Player:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.key = None
        self.hand = []

    def set_key(self, key):
        self.key = key

    def add_card(self, card):
        self.hand.append(card)

    def remove_card(self, card):
        self.hand.remove(card)

    def get_decrypted_hand(self):
        return [Crypto.decrypt(card, self.key) for card in self.hand]

class Game:
    def __init__(self):
        self.players = {}
        self.deck = Deck()
        self.started = False
        self.current_player = None
        self.group_chat_id = None
        self.table = []

    def add_player(self, user_id, username):
        if len(self.players) < NUM_PLAYERS and user_id not in self.players:
            self.players[user_id] = Player(user_id, username)
            return True
        return False

    def all_keys_set(self):
        return all(player.key is not None for player in self.players.values())

    def encrypt_deck(self):
        for player in self.players.values():
            self.deck.cards = [Crypto.encrypt(f"{card.rank}{card.suit}", player.key) for card in self.deck.cards]
        self.deck.shuffle()

    def deal_cards(self):
        for _ in range(5):
            for player in self.players.values():
                card = self.deck.draw()
                if card:
                    player.add_card(card)

    def start_game(self):
        self.encrypt_deck()
        self.deal_cards()
        self.started = True
        self.current_player = next(iter(self.players))

    def next_player(self):
        player_ids = list(self.players.keys())
        current_index = player_ids.index(self.current_player)
        self.current_player = player_ids[(current_index + 1) % len(player_ids)]

    def get_playable_cards(self):
        return self.players[self.current_player].get_decrypted_hand()

    def play_card(self, player, card):
        self.table.append((player.username, card))

    def draw_card(self, player_id):
        if player_id in self.players and self.deck.cards:
            player = self.players[player_id]
            drawn_card = self.deck.draw()
            if drawn_card:
                player.add_card(drawn_card)
                return True
        return False