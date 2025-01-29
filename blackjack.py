"""
blackjack things for rl
- maximum resulting hands from splitting is MAX_RESPLIT + 1
- resplit aces and insurance allowed
- double on any pair
"""

from collections import deque
from enum import Enum
import random


CARDS_PER_DECK = 52
MAX_RESPLIT = 3


class CardValue(Enum):
    """
    enum of card values
    """

    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13


class CardSuit(Enum):
    """
    enum of card suits
    """

    CLUBS = 1
    DIAMONDS = 2
    HEARTS = 3
    SPADES = 4


class Card:
    """
    represents a single card
    """

    def __init__(self, value, suit):
        self.value = value
        self.suit = suit

    def __repr__(self):
        return f"{self.value.value}{self.suit.name[0]}"

    def __str__(self):
        return f"{self.value.value}{self.suit.name[0]}"

    def describe(self):
        return f"{self.value.name.lower().capitalize()} of {self.suit.name.lower().capitalize()}"

    def is_paint(self):
        return (
            True
            if self.value
            in (CardValue.TEN, CardValue.JACK, CardValue.QUEEN, CardValue.KING)
            else False
        )

    def is_ace(self):
        return True if self.value is CardValue.ACE else False


class Deck:
    """
    represents a 52-card deck of cards
    """

    def __init__(self):
        self.cards = deque()
        for suit in CardSuit:
            for value in CardValue:
                card = Card(value, suit)
                self.cards.append(card)


class Shoe:
    """
    represents a blackjack shoe
    - decks: number of decks
    - cut_card_pos: number of cards behind the cut card
    """

    def __init__(self, decks, cut_card_pos=2 * CARDS_PER_DECK):
        self.decks = decks
        self.cards = deque()
        self.cut_card_pos = cut_card_pos
        self.cut_card_out = False

        for _ in range(self.decks):
            new_deck = Deck()
            self.cards += new_deck.cards

        # shuffle
        random.shuffle(self.cards)

        # burn a card
        self.deal_cards(1)

    def deal_cards(self, number):
        cards = []
        if len(self.cards) - number <= self.cut_card_pos:
            self.cut_card_out = True
        for _ in range(number):
            cards.append(self.cards.popleft())
        return cards


class Hand:
    """
    base class for hands
    """

    def __init__(self, cards):
        self.cards = cards

    def __str__(self):
        return f"Hand<{ [c for c in self.cards] }>"

    def __repr__(self):
        return f"Hand<{ [c for c in self.cards] }>"

    def is_soft(self):
        """
        a soft hand has at least one ace and at least one ace must be interpretable as both 1 and 11, so it will not bust.  this is
        true for at least one ace when the hand total interpretting aces as 1 is less than or equal to 11.
        """
        return any(map(lambda x: x.is_ace(), self.cards)) and sum([c.value.value for c in self.cards]) <= 11

    def is_bust(self):
        return (
            sum(
                [
                    c.value.value if c.value.value not in (10, 11, 12, 13) else 10
                    for c in self.cards
                ]
            )
            > 21
        )

    def is_bj(self):
        return (self.cards[0].is_ace() and self.cards[1].is_paint()) or (
            self.cards[0].is_paint() and self.cards[1].is_ace()
        )


class DealerHand(Hand):
    """
    represents a dealer's hand
    """

    def __init__(self, cards):
        super().__init__(cards)


class PlayerHand(Hand):
    """
    represents a player's hand
    """

    def __init__(self, cards, bet):
        super().__init__(cards)
        self.bet = bet
        self.is_doubled = False

    def split(self, new_cards):
        h1 = PlayerHand([self.cards[0], new_cards[0]], self.bet)
        h2 = PlayerHand([self.cards[1], new_cards[1]], self.bet)
        return h1, h2

    def is_pair(self):
        return self.cards[0].value is self.cards[1].value

    def is_soft(self):
        return any(map(lambda x: x.is_ace(), self.cards))


class Player:
    """
    represents a player
    """

    def __init__(self, takes_insurance=False):
        self.takes_insurance = takes_insurance
        self.money = 10000
        self.hands = []
        self.stayed_hands = []

    def get_bet_amount(self):
        return 100

    def lose(self, amt):
        self.money -= amt

    def win(self, amt):
        self.money += amt

    def splits(self, player_hand, dealer_card):
        return True if random.random() < 0.5 else False

    def doubles(self, player_hand, dealer_card):
        return True if random.random() < 0.5 else False

    def hits(self, player_hand, dealer_card):
        return True if random.random() < 0.5 else False


class Game:
    """
    represents a shoe of game play
    """

    def __init__(self, shoe, players):
        self.shoe = shoe
        self.players = players

    def process_post_split(self, hand, dealer_card, player_id):
        """
        double and hit processing
        - put in container player.stayed_hands if not broken
        - lose function if broken
        """
        # player
        player = self.players[player_id]

        # double
        if player.doubles(hand, dealer_card):
            hand.bet = 2 * hand.bet
            double_card = self.shoe.deal_cards(1)
            hand.cards += double_card
            if hand.is_bust():
                player.lose(hand.bet)
            else:
                hand.is_doubled = True
                player.stayed_hands.append(hand)
            return

        # hit or stay in while loop
        while not hand.is_bust() and player.hits(hand, dealer_card):
            hit_card = self.shoe.deal_cards(1)
            hand.cards += hit_card
            if hand.is_bust():
                player.lose(hand.bet)
                return

        # lose or put in container
        player.stayed_hands.append(hand)

    def process_hand(self, hand, dealer_card, player_id, total_splits):
        """
        top level hand processor
        - uses recursion to handle splitting
        """
        player = self.players[player_id]
        if hand.is_pair() and player.splits(hand, dealer_card):
            if total_splits < MAX_RESPLIT:
                h1, h2 = hand.split(self.shoe.deal_cards(2))
                self.process_hand(h1, dealer_card, player_id, total_splits + 1)
                self.process_hand(h2, dealer_card, player_id, total_splits + 1)
            else:
                self.process_post_split(hand, dealer_card, player_id)
        else:
            self.process_post_split(hand, dealer_card, player_id)

    def process_round(self):
        """
        top level round processor
        """
        # deal hands
        dealer_hand = DealerHand(self.shoe.deal_cards(2))
        for player in self.players:
            player.hands.append(
                PlayerHand(self.shoe.deal_cards(2), player.get_bet_amount())
            )

        # handle insurance
        if dealer_hand.cards[1].is_ace():
            for player in self.players:
                if player.takes_insurance:
                    for hand in player.hands:
                        if dealer_hand.cards[0].is_paint():
                            player.win(hand.bet)
                        else:
                            player.lose(0.5 * hand.bet)

        # handle dealer blackjack
        if dealer_hand.is_bj():
            for player in self.players:
                for hand in player.hands:
                    if not hand.is_bj():
                        player.lose(hand.bet)
            return

        # handle player blackjacks
        for player in self.players:
            for hand in player.hands:
                if hand.is_bj():
                    player.win(1.5 * player.get_bet_amount())

        # handle player hands
        for i, player in enumerate(self.players):
            for hand in player.hands:
                if not hand.is_bj():
                    self.process_hand(hand, dealer_hand.cards[1], i, 0)

        # handle dealer hand

        # payoff stayed hands or take bets

        # clear
        for player in self.players:
            player.hands = []
            player.stayed_hands = []

    def run(self):
        while not self.shoe.cut_card_out:
            self.process_round()
        for i, agent in enumerate(self.players):
            print(i, agent.money)


# create 6-deck shoe
shoe = Shoe(6)

# create two players
a = Player(takes_insurance=True)
b = Player(takes_insurance=False)

# play all rounds in the shoe
g = Game(shoe, [a, b])
g.run()
