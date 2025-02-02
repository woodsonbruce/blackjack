"""
blackjack simulation
- resplit aces and insurance allowed
- double on any pair
"""

from collections import deque
from enum import Enum
import logging
import random


# create logger
logging.basicConfig(
    filename="session.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)

# Creating an object
logger = logging.getLogger()

# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)

# game constants
CARDS_PER_DECK = 52
MAX_RESPLIT = 4
MAX_TABLE_SPOTS = 7
DEALER_HITS_SOFT_17 = False
NUMBER_SHOES_IN_SIMULATION = 1000
TEN_CARDS = (10, 11, 12, 13)
STIFF_TOTALS = (12, 13, 14, 15, 16)
DEFAULT_BET = 100
DEFAULT_STAKE = 100000


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

    @classmethod
    def as_char(cls, value):
        """
        returns a one-char representation of the card value
        """
        codes = {
            1: "A",
            2: "2",
            3: "3",
            4: "4",
            5: "5",
            6: "6",
            7: "7",
            8: "8",
            9: "9",
            10: "T",
            11: "J",
            12: "Q",
            13: "K",
        }
        return codes[value]


class CardSuit(Enum):
    """
    enum of card suits
    """

    CLUBS = 1
    DIAMONDS = 2
    HEARTS = 3
    SPADES = 4

    @classmethod
    def as_unicode(cls, value):
        """
        returns a unicode char for the suit
        """
        codes = {
            1: "♣",
            2: "♦",
            3: "♥",
            4: "♠",
        }
        return codes[value]

    @classmethod
    def as_char(cls, value):
        """
        returns a char representation of the suit
        """
        codes = {
            1: "C",
            2: "D",
            3: "H",
            4: "S",
        }
        return codes[value]


class PlayerStrategy(Enum):
    """
    enum of possible strategies
    """

    BASIC = 1
    RANDOM = 2
    Q_LEARN = 3


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
        return f"{self.value.as_char(self.value.value)}{self.suit.as_char(self.suit.value)}"

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

    def is_soft(self):
        """
        whether a hand is soft or not
        """
        return (
            any(map(lambda x: x.is_ace(), self.cards))
            and sum(
                [
                    c.value.value if c.value.value not in TEN_CARDS else 10
                    for c in self.cards
                ]
            )
            <= 11
        )

    def is_bust(self):
        """
        whether the hand is above 21 with every ace counted low
        """
        return (
            sum(
                [
                    c.value.value if c.value.value not in TEN_CARDS else 10
                    for c in self.cards
                ]
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
                c.value.value if c.value.value not in TEN_CARDS else 10
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

    def __repr__(self):
        """
        describes a dealer hand
        """
        return f"DealererHand<hole card:{self.cards[0]}, showing:{self.cards[1]}>"

    def dealer_hits(self):
        """
        whether a dealer hits a hand
        """
        if not self.is_soft():
            return self.get_sum() < 17
        if DEALER_HITS_SOFT_17:
            return self.get_sum() <= 17
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
        # self.surrender_decisions = []
        # self.pair_decisions = []
        # self.double_decisions = []
        # self.hit_stand_decisions = []

    def __repr__(self):
        """
        describes a player hand
        """
        return f"PlayerHand<{self.cards}>"

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

    def __init__(
        self,
        name,
        money=DEFAULT_STAKE,
        strategy=PlayerStrategy.RANDOM,
        takes_insurance=False,
    ):
        """
        constructs a player
        """
        self.name = name
        self.money = money
        self.strategy = strategy
        self.takes_insurance = takes_insurance

    def __repr__(self):
        """
        describes a player
        """
        return self.name

    def get_bet_amount(self):
        """
        get the amount the player wants to bet
        """
        return DEFAULT_BET

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
        if self.strategy == PlayerStrategy.RANDOM:
            return random.choice([True, False])
        if self.strategy == PlayerStrategy.BASIC:
            return self.__splits_basic(player_hand, dealer_card)

    def __splits_basic(self, player_hand, dealer_card):
        """
        whether a player splits a hand according to basic strategy
        """
        if player_hand.cards[0].value in (CardValue.EIGHT, CardValue.ACE):
            return True
        if player_hand.cards[0].value in (
            CardValue.TWO,
            CardValue.THREE,
            CardValue.SEVEN,
        ):
            if dealer_card.value in (
                CardValue.TWO,
                CardValue.THREE,
                CardValue.FOUR,
                CardValue.FIVE,
                CardValue.SIX,
                CardValue.SEVEN,
            ):
                return True
        if player_hand.cards[0].value is CardValue.FOUR:
            if dealer_card.value in (CardValue.FIVE, CardValue.SIX):
                return True
        if player_hand.cards[0].value is CardValue.SIX:
            if dealer_card.value in (
                CardValue.TWO,
                CardValue.THREE,
                CardValue.FOUR,
                CardValue.FIVE,
                CardValue.SIX,
            ):
                return True
        if player_hand.cards[0].value is CardValue.NINE:
            if dealer_card.value in (
                CardValue.TWO,
                CardValue.THREE,
                CardValue.FOUR,
                CardValue.FIVE,
                CardValue.SIX,
                CardValue.EIGHT,
                CardValue.NINE,
            ):
                return True
        return False

    def doubles(self, player_hand, dealer_card):
        """
        whether a player doubles a hand
        """
        if self.strategy == PlayerStrategy.RANDOM:
            return random.choice([True, False])
        if self.strategy == PlayerStrategy.BASIC:
            return self.__doubles_basic(player_hand, dealer_card)

    def __doubles_basic(self, player_hand, dealer_card):
        """
        whether a player doubles a hand according to basic strategy
        """
        if not player_hand.is_soft():
            if player_hand.get_sum() == 9:
                if dealer_card.value in (
                    CardValue.THREE,
                    CardValue.FOUR,
                    CardValue.FIVE,
                    CardValue.SIX,
                ):
                    return True
            elif player_hand.get_sum() == 10:
                if dealer_card.value in (
                    CardValue.TWO,
                    CardValue.THREE,
                    CardValue.FOUR,
                    CardValue.FIVE,
                    CardValue.SIX,
                    CardValue.SEVEN,
                    CardValue.EIGHT,
                    CardValue.NINE,
                ):
                    return True
            elif player_hand.get_sum() == 11:
                if dealer_card.value in (
                    CardValue.TWO,
                    CardValue.THREE,
                    CardValue.FOUR,
                    CardValue.FIVE,
                    CardValue.SIX,
                    CardValue.SEVEN,
                    CardValue.EIGHT,
                    CardValue.NINE,
                    CardValue.TEN,
                ):
                    return True
        else:  # is soft
            if CardValue.TWO in tuple(
                c.value for c in player_hand.cards
            ) or CardValue.THREE in tuple(c.value for c in player_hand.cards):
                if dealer_card.value in (
                    CardValue.FIVE,
                    CardValue.SIX,
                ):
                    return True
            if CardValue.FOUR in tuple(
                c.value for c in player_hand.cards
            ) or CardValue.FIVE in tuple(c.value for c in player_hand.cards):
                if dealer_card.value in (
                    CardValue.FOUR,
                    CardValue.FIVE,
                    CardValue.SIX,
                ):
                    return True
            if CardValue.SIX in tuple(
                c.value for c in player_hand.cards
            ) or CardValue.SEVEN in tuple(c.value for c in player_hand.cards):
                if dealer_card.value in (
                    CardValue.THREE,
                    CardValue.FOUR,
                    CardValue.FIVE,
                    CardValue.SIX,
                ):
                    return True
        return False

    def hits(self, player_hand, dealer_card):
        """
        whether a player hits a hand
        """
        if self.strategy == PlayerStrategy.RANDOM:
            return random.choice([True, False])
        if self.strategy == PlayerStrategy.BASIC:
            return self.__hits_basic(player_hand, dealer_card)

    def __hits_basic(self, player_hand, dealer_card):
        """
        whether a player hits a hand according to basic strategy
        """
        if player_hand.get_sum() < 12:
            return True
        if player_hand.get_sum() == 12:
            if dealer_card.value not in (
                CardValue.FOUR,
                CardValue.FIVE,
                CardValue.SIX,
            ):
                return True
        if player_hand.get_sum() in STIFF_TOTALS:
            if dealer_card.value not in (
                CardValue.TWO,
                CardValue.THREE,
                CardValue.FOUR,
                CardValue.FIVE,
                CardValue.SIX,
            ):
                return True
        return False


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
        # self.insurance_decisions = []


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
            msg = f"{spots_req} spots needed but table has {MAX_TABLE_SPOTS}"
            logger.error(msg)
            raise TooManyPlayersException(msg)

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
                logger.info(
                    "player %s doubles hand %s with card %s",
                    spot.player,
                    hand,
                    double_card,
                )
                hand.cards += double_card
                hand.is_doubled = True
            if hand.is_bust():
                index_busted.append(i)
                spot.player.lose(hand.bet)
                logger.info("player %s busts and loses %d", spot.player, hand.bet)
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
                    logger.info(
                        "player %s hitting hand %s with %s", spot.player, hand, hit_card
                    )
                    hand.cards += hit_card
                    if hand.is_bust():
                        index_busted.append(i)
                        spot.player.lose(hand.bet)
                        logger.info(
                            "player %s busts and loses %d", spot.player, hand.bet
                        )
                if not hand.is_bust():
                    logger.info("player %s stands %s", spot.player, hand)

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
            logger.info(
                "player %s splits hand %s into hands %s and %s",
                spot.player,
                hand,
                h1,
                h2,
            )
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
        logger.info("dealer hand: %s", dealer_hand)

        # create player hands
        for spot in self.spots:
            spot.hands.append(
                PlayerHand(self.shoe.deal_cards(2), spot.player.get_bet_amount())
            )
            logger.info("player hand (%s): %s", spot.player, spot.hands[0])

        # handle insurance bets
        if dealer_hand.cards[1].is_ace():
            logger.info("dealer has an ace so taking insurance bets")
            for spot in self.spots:
                if spot.player.takes_insurance:
                    if dealer_hand.cards[0].is_paint():
                        spot.player.win(spot.hands[0].bet)
                        logger.info(
                            "dealer has blackjack, player %s wins insurance bet %d",
                            spot.player,
                            spot.hands[0].bet,
                        )
                    else:
                        spot.player.lose(0.5 * spot.hands[0].bet)
                        logger.info(
                            "dealer does not have blackjack, player %s loses insurance bet %d",
                            spot.player,
                            spot.hands[0].bet,
                        )

        # handle dealer blackjack case
        if dealer_hand.is_bj():
            logger.info("dealer has blackjack")
            for spot in self.spots:
                if not spot.hands[0].is_bj():
                    spot.player.lose(spot.hands[0].bet)
                    logger.info(
                        "player %s loses %d",
                        spot.player,
                        spot.hands[0].bet,
                    )
                spot.hands = []
            return

        # handle player blackjacks
        for spot in self.spots:
            if spot.hands[0].is_bj():
                win = 1.5 * spot.hands[0].bet
                spot.player.win(win)
                logger.info(
                    "player %s has blackjack, wins %d",
                    spot.player,
                    win,
                )
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

    def play_entire_shoe(self):
        """
        play all rounds in the shoe
        """
        round_number = 1
        while not self.shoe.cut_card_out:
            logger.info("dealing round %d", round_number)
            self.process_round()
            for player in self.players:
                logger.info(
                    "player %s has %d after round %d",
                    player,
                    player.money,
                    round_number,
                )
            round_number += 1


class Decision:
    """
    represents a blackjack decision
    """

    def __init__(self, player_hand, dealer_card, value):
        self.player_hand = player_hand
        self.dealer_card = dealer_card
        self.value = value


class KnownOutcomeDecision(Decision):
    """
    represents a completed blackjack decision
    """

    def __init__(self, decision, did_win, number_steps):
        super().__init__(decision.player_hand, decision.dealer_card, decision.value)
        self.did_win = did_win
        self.number_discount_steps = number_steps


class QLearner:
    """
    class to hold and update decision data and default decisions for a
    q learning decision category, eg insurance, surrender, split, double,
    hit, and stand
    """

    def __init__(self):
        self.decision_data = []

        # populate with random bool values to start
        self.two_card_decisions = {}
        self.card_sum_decisions = {}

    @classmethod
    def __get_two_card_decision_key(cls, player_hand, dealer_card):
        """
        returns a key for use in the decision dictionary
        """
        player_vals = sorted(
            [
                CardValue.as_char(player_hand.cards[0].value.value),
                CardValue.as_char(player_hand.cards[1].value.value),
            ]
        )
        dealer_val = CardValue.as_char(dealer_card.value.value)
        return player_vals[0] + player_vals[1] + dealer_val

    def add_decision(self, decision):
        """
        adds known outcome decision
        - player cards
        - dealer card
        - decision
        - outcome
        - discount steps

        """
        self.decision_data.append(data)

    def update_decisions(self):
        """
        updates decisions based on decision data
        """
        pass

    def get_two_card_decision(self, player_hand, dealer_card):
        """
        gets the decision based on two cards
        """
        pass

    def get_hand_sum_decision(self, hand_sum, dealer_card):
        """
        gets the decision based on hand sum
        """

    def test(self, p, d):
        return self.__class__.__get_two_card_decision_key(p, d)


# start simulation
logger.info("starting simulation")

# create two players
john = Player("John", strategy=PlayerStrategy.RANDOM, takes_insurance=True)
logger.info(
    "player %s with strategy %s and takes insurance %s created",
    john,
    john.strategy.name.lower(),
    str(john.takes_insurance),
)

katy = Player("Katy", strategy=PlayerStrategy.BASIC, takes_insurance=False)
logger.info(
    "player %s with strategy %s and takes insurance %s created",
    katy,
    katy.strategy.name.lower(),
    str(katy.takes_insurance),
)

# play specified numbr of shoes
for shoe_number in range(NUMBER_SHOES_IN_SIMULATION):
    logger.info("starting shoe number %d", shoe_number)
    six_deck_shoe = Shoe(6)
    g = Game(six_deck_shoe, player_spot_data=[(john, 1), (katy, 3)])
    g.play_entire_shoe()

logger.info("ending simulation")
