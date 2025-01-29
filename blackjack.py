"""
blackjack simulation
- resplit aces and insurance allowed
- double on any pair
"""

from collections import deque
from enum import Enum
import random


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
        return (
            any(map(lambda x: x.is_ace(), self.cards))
            and sum(
                [
                    c.value.value if c.value.value not in (10, 11, 12, 13) else 10
                    for c in self.cards
                ]
            )
            <= 11
        )

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
        super().__init__(cards)

    def dealer_hits(self):

        if not self.is_soft():
            if self.get_sum() < 17:
                return True
            else:
                return False
        else:
            if DEALER_HITS_SOFT_17:
                if self.get_sum() < 18:
                    return True
            else:
                if self.get_sum() < 17:
                    True
            return False


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


class Player:
    """
    represents a player
    """

    def __init__(self, takes_insurance=False):
        self.takes_insurance = takes_insurance
        self.money = 10000

        # to delete
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


class Spot:
    """
    represents a spot at the table
    - takes one hand and one bet
    - controlled by a player
    - player can control more than one adjacent spots
    """

    def __init__(self, table_position):
        self.table_position = table_position
        self.player = None
        self.hands = []


class TooManyPlayersException(Exception):
    pass


class Game:
    """
    represents a shoe of game play
    """

    def __init__(self, shoe, player_spot_data):

        # ensure all players can play specified hands
        total_spots_required = sum([_[1] for _ in player_spot_data])
        if total_spots_required > MAX_TABLE_SPOTS:
            raise TooManyPlayersException(
                f"{total_spots_required} spots needed but table has {MAX_TABLE_SPOTS}"
            )

        # set shoe
        self.shoe = shoe

        # create spots
        self.spots = []
        for i in range(total_spots_required):
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

    def process_double_downs(self, dealer_card, spot):
        index_busted = []  # some players double twelve
        for i, hand in enumerate(spot.hands):
            if spot.player.doubles(hand, dealer_card):
                hand.bet = 2 * hand.bet
                double_card = self.shoe.deal_cards(1)
                hand.cards += double_card
            if hand.is_bust():
                index_busted.append(i)
                spot.player.lose(hand.bet)
            else:
                hand.is_doubled = True
        for i in sorted(index_busted, reverse=True):
            del spot.hands[i]

    def process_hit_stand(self, dealer_card, spot):
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

    def process_splitting(self, hand, dealer_card, spot):
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
            self.process_splitting(h1, dealer_card, spot)
            self.process_splitting(h2, dealer_card, spot)

    def process_spot(self, spot, dealer_card):
        self.process_splitting(spot.hands[0], dealer_card, spot)
        self.process_double_downs(dealer_card, spot)
        self.process_hit_stand(dealer_card, spot)

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
            return

        # handle player blackjacks
        for spot in self.spots:
            if spot.hands[0].is_bj():
                spot.player.win(1.5 * spot.hands[0].bet)
                spot.hands = []

        # handle player hands by spot position
        for spot in self.spots:
            if spot.hands:
                self.process_spot(spot, dealer_hand.cards[1])

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
        while not self.shoe.cut_card_out:
            self.process_round()
        for i, agent in enumerate(self.players):
            print(i, agent.money)


# create two players
a = Player(takes_insurance=True)
b = Player(takes_insurance=False)

# play all rounds in the shoe
for _ in range(10):
    print("---")
    shoe = Shoe(6)
    g = Game(shoe, player_spot_data=[(a, 4), (b, 3)])
    g.run()
