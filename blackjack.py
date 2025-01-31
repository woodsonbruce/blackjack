"""
blackjack simulation
- resplit aces and insurance allowed
- double on any pair
"""

from collections import deque
from enum import Enum
import random


# game constants
CARDS_PER_DECK = 52
MAX_RESPLIT = 4
MAX_TABLE_SPOTS = 7
DEALER_HITS_SOFT_17 = False


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
        """
        constructs a card
        """
        self.value = value
        self.suit = suit

    def __repr__(self):
        """
        describes card
        """
        return f"{self.value.value}{self.suit.name[0]}"

    def as_text(self):
        """
        get lengthy description, eg 'ten of diamonds'
        """
        return f"{self.value.name.lower().capitalize()} of {self.suit.name.lower().capitalize()}"

    def is_paint(self):
        """
        whether a card is a ten, jack, queen, or king
        """
        return self.value in (
            CardValue.TEN,
            CardValue.JACK,
            CardValue.QUEEN,
            CardValue.KING,
        )

    def is_ace(self):
        """
        whether a card is an ace
        """
        return self.value is CardValue.ACE


class Deck:
    """
    represents a 52-card deck of cards
    """

    def __init__(self):
        """
        constructs a deck
        """
        self.cards = deque()
        for suit in CardSuit:
            for value in CardValue:
                card = Card(value, suit)
                self.cards.append(card)


class Shoe:
    """
    represents a blackjack shoe
    """

    def __init__(self, decks, cut_card_pos=2 * CARDS_PER_DECK):
        """
        constructs a shoe
        """
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
        """
        deal specified number of cards out of the front
        """
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
        """
        constructs base-class components of a hand
        """
        self.cards = cards

    def __repr__(self):
        """
        describes a shoe
        """
        return f"Hand<{self.cards}>"

    def is_soft(self):
        """
        whether a hand is soft or not
        """
        tens = (10, 11, 12, 13)
        return (
            any(map(lambda x: x.is_ace(), self.cards))
            and sum(
                [c.value.value if c.value.value not in tens else 10 for c in self.cards]
            )
            <= 11
        )

    def is_bust(self):
        """
        whether the hand is above 21 with every ace counted low
        """
        tens = (10, 11, 12, 13)
        return (
            sum(
                [c.value.value if c.value.value not in tens else 10 for c in self.cards]
            )
            > 21
        )

    def is_bj(self):
        """
        whether the hand is a blackjack
        """
        return (self.cards[0].is_ace() and self.cards[1].is_paint()) or (
            self.cards[0].is_paint() and self.cards[1].is_ace()
        )

    def get_sum(self):
        """
        count aces high unless it busts the hand
        """
        # get initial value with aces counted low
        value = sum(
            [
                c.value.value if c.value.value not in (10, 11, 12, 13) else 10
                for c in self.cards
            ]
        )

        # if there are aces, count one as high
        return (
            value + 10
            if value <= 11 and CardValue.ACE in tuple(c.value for c in self.cards)
            else value
        )


class DealerHand(Hand):
    """
    represents a dealer's hand
    """

    def __init__(self, cards):
        """
        constructs a dealer's hand
        """
        super().__init__(cards)

    def dealer_hits(self):
        """
        whether a dealer hits a hand
        """
        if not self.is_soft():
            return self.get_sum() < 17
        if DEALER_HITS_SOFT_17:
            return self.get_sum() < 18
        return self.get_sum() < 17


class PlayerHand(Hand):
    """
    represents a player's hand
    """

    def __init__(self, cards, bet):
        """
        constructs a player's hand
        """
        super().__init__(cards)
        self.bet = bet
        self.is_doubled = False

    def split(self, new_cards):
        """
        splits a hand
        """
        h1 = PlayerHand([self.cards[0], new_cards[0]], self.bet)
        h2 = PlayerHand([self.cards[1], new_cards[1]], self.bet)
        return h1, h2

    def is_pair(self):
        """
        whether a hand is a pair
        """
        return self.cards[0].value is self.cards[1].value


class Player:
    """
    represents a player
    """

    def __init__(self, name, takes_insurance=False):
        """
        constructs a player
        """
        self.takes_insurance = takes_insurance
        self.money = 10000
        self.name = name

    def __repr__(self):
        """
        describes a player
        """
        return self.name

    def get_bet_amount(self):
        """
        get the amount the player wants to bet
        """
        return 100

    def lose(self, amt):
        """
        player loses a bet
        """
        self.money -= amt

    def win(self, amt):
        """
        player wins a bet
        """
        self.money += amt

    def splits(self, player_hand, dealer_card):
        """
        whether a player splits a hand
        """
        return random.random() < 0.5

    def doubles(self, player_hand, dealer_card):
        """
        whether a player doubles a hand
        """
        return random.random() < 0.5

    def hits(self, player_hand, dealer_card):
        """
        whether a player hits a hand
        """
        return random.random() < 0.5


class Spot:
    """
    represents a spot at the table
    - insurance bets are per spot
    - has a single hand and a single bet initially
    - hands may split and/or be doubled
    - player can play multiple spots
    """

    def __init__(self, table_position):
        """
        constructs a spot
        """
        self.table_position = table_position
        self.player = None
        self.hands = []


class TooManyPlayersException(Exception):
    """
    exception class for insufficient player spots
    """


class Game:
    """
    represents a shoe of game play
    """

    def __init__(self, shoe, player_spot_data):
        """
        constructs a game
        """

        # ensure all players can play specified hands
        spots_req = sum([_[1] for _ in player_spot_data])
        if spots_req > MAX_TABLE_SPOTS:
            raise TooManyPlayersException(
                f"{spots_req} spots needed but table has {MAX_TABLE_SPOTS}"
            )

        # set shoe
        self.shoe = shoe

        # create spots
        self.spots = []
        for i in range(spots_req):
            self.spots.append(Spot(i))

        # set player data
        self.number_players = len(player_spot_data)
        self.players = [_[0] for _ in player_spot_data]

        # assign players to spots
        next_spot_index = 0
        for datum in player_spot_data:
            for _ in range(datum[1]):
                self.spots[next_spot_index].player = datum[0]
                next_spot_index += 1

    def __process_double_downs(self, dealer_card, spot):
        """
        handles doubling down
        """
        index_busted = []  # some players double twelve
        for i, hand in enumerate(spot.hands):
            if spot.player.doubles(hand, dealer_card):
                hand.bet = 2 * hand.bet
                double_card = self.shoe.deal_cards(1)
                hand.cards += double_card
                hand.is_doubled = True
            if hand.is_bust():
                index_busted.append(i)
                spot.player.lose(hand.bet)
        for i in sorted(index_busted, reverse=True):
            del spot.hands[i]

    def __process_hit_stand(self, dealer_card, spot):
        """
        handles hitting or standing
        """
        index_busted = []
        for i, hand in enumerate(spot.hands):
            if not hand.is_doubled:
                while not hand.is_bust() and spot.player.hits(hand, dealer_card):
                    hit_card = self.shoe.deal_cards(1)
                    hand.cards += hit_card
                    if hand.is_bust():
                        index_busted.append(i)
                        spot.player.lose(hand.bet)
        for i in sorted(index_busted, reverse=True):
            del spot.hands[i]

    def __process_splitting(self, hand, dealer_card, spot):
        """
        use recursion to handle splitting
        """
        if (
            hand.is_pair()
            and spot.player.splits(hand, dealer_card)
            and len(spot.hands) < MAX_RESPLIT
        ):
            h1, h2 = hand.split(self.shoe.deal_cards(2))
            spot.hands.remove(hand)
            spot.hands.append(h1)
            spot.hands.append(h2)
            self.__process_splitting(h1, dealer_card, spot)
            self.__process_splitting(h2, dealer_card, spot)

    def __process_spot(self, spot, dealer_card):
        """
        handle player decisions after processing insurance bets and blackjacks
        """
        self.__process_splitting(spot.hands[0], dealer_card, spot)
        self.__process_double_downs(dealer_card, spot)
        self.__process_hit_stand(dealer_card, spot)

    def process_round(self):
        """
        process a round
        """
        # create dealer hand
        dealer_hand = DealerHand(self.shoe.deal_cards(2))

        # create player hands
        for spot in self.spots:
            spot.hands.append(
                PlayerHand(self.shoe.deal_cards(2), spot.player.get_bet_amount())
            )

        # handle insurance bets
        if dealer_hand.cards[1].is_ace():
            for spot in self.spots:
                if spot.player.takes_insurance:
                    if dealer_hand.cards[0].is_paint():
                        spot.player.win(spot.hands[0].bet)
                    else:
                        spot.player.lose(0.5 * spot.hands[0].bet)

        # handle dealer blackjack case
        if dealer_hand.is_bj():
            for spot in self.spots:
                if not spot.hands[0].is_bj():
                    spot.player.lose(spot.hands[0].bet)
                spot.hands = []
            return

        # handle player blackjacks
        for spot in self.spots:
            if spot.hands[0].is_bj():
                spot.player.win(1.5 * spot.hands[0].bet)
                spot.hands = []

        # handle player hands by spot position
        for spot in self.spots:
            if spot.hands:
                self.__process_spot(spot, dealer_hand.cards[1])

        # handle dealer hand
        while dealer_hand.dealer_hits():
            hit_card = self.shoe.deal_cards(1)
            dealer_hand.cards += hit_card

        # payoff stayed hands or take bets
        if dealer_hand.is_bust():
            for spot in self.spots:
                for hand in spot.hands:
                    spot.player.win(hand.bet)
        else:
            for spot in self.spots:
                for hand in spot.hands:
                    if hand.get_sum() > dealer_hand.get_sum():
                        spot.player.win(hand.bet)
                    elif hand.get_sum() < dealer_hand.get_sum():
                        spot.player.lose(hand.bet)

        # clear
        for spot in self.spots:
            spot.hands = []

    def run(self):
        """
        play all rounds in the shoe
        """
        while not self.shoe.cut_card_out:
            self.process_round()
        for player in self.players:
            print(f"player {player} has {player.money} after round")


# create two players
a = Player("John", takes_insurance=True)
b = Player("Katy", takes_insurance=False)

# play all rounds in the shoe
for _ in range(10):
    print("---")
    six_deck_shoe = Shoe(6)
    g = Game(six_deck_shoe, player_spot_data=[(a, 1), (b, 3)])
    g.run()
