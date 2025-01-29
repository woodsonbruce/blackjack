"""
tests for blackjack program
"""
from blackjack import *


def test_hand_is_bj():
    ace_clubs = Card(CardValue.ACE, CardSuit.CLUBS)
    ten_diamonds = Card(CardValue.TEN, CardSuit.DIAMONDS)
    hand = Hand([ace_clubs, ten_diamonds])
    assert hand.is_bj()

def test_hand_is_not_bj():
    ace_clubs = Card(CardValue.ACE, CardSuit.CLUBS)
    ace_diamonds = Card(CardValue.ACE, CardSuit.DIAMONDS)
    hand = Hand([ace_clubs, ace_diamonds])
    assert not hand.is_bj()

def test_hand_is_soft():
    ace_clubs = Card(CardValue.ACE, CardSuit.CLUBS)
    ten_diamonds = Card(CardValue.TEN, CardSuit.DIAMONDS)
    hand = Hand([ace_clubs, ten_diamonds])
    assert hand.is_soft()

def test_hand_is_not_soft():
    nine_clubs = Card(CardValue.NINE, CardSuit.CLUBS)
    ten_diamonds = Card(CardValue.TEN, CardSuit.DIAMONDS)
    hand = Hand([nine_clubs, ten_diamonds])
    assert not hand.is_soft()

def test_hand_with_aces_is_not_soft():
    nine_clubs = Card(CardValue.NINE, CardSuit.CLUBS)
    ten_diamonds = Card(CardValue.TEN, CardSuit.DIAMONDS)    
    ace_diamonds = Card(CardValue.ACE, CardSuit.DIAMONDS)
    hand = Hand([nine_clubs, ten_diamonds, ace_diamonds])
    assert not hand.is_soft()

def test_hand_is_bust():
    five_clubs = Card(CardValue.FIVE, CardSuit.CLUBS)
    ten_diamonds = Card(CardValue.TEN, CardSuit.DIAMONDS)
    seven_hearts = Card(CardValue.SEVEN, CardSuit.HEARTS)
    hand = Hand([five_clubs, ten_diamonds, seven_hearts])
    assert hand.is_bust()

def test_hand_is_not_bust():
    ace_clubs = Card(CardValue.ACE, CardSuit.CLUBS)
    ten_diamonds = Card(CardValue.TEN, CardSuit.DIAMONDS)
    hand = Hand([ace_clubs, ten_diamonds])
    assert not hand.is_bust()

def test_soft_hand_is_not_bust():
    """
    assume a player gets a pair of aces, does not split, keeps hitting and
    getting only aces in an hypothetical shoe until the hand is hard 21
    """
    ace_clubs = Card(CardValue.ACE, CardSuit.CLUBS)
    ace_diamonds = Card(CardValue.ACE, CardSuit.DIAMONDS)
    ace_hearts = Card(CardValue.ACE, CardSuit.HEARTS)
    ace_spades = Card(CardValue.ACE, CardSuit.SPADES)

    hand = Hand([
        ace_clubs,
        ace_clubs,
        ace_clubs,
        ace_clubs,
        ace_clubs,
        ace_clubs,
        ace_diamonds,
        ace_diamonds,
        ace_diamonds,
        ace_diamonds,
        ace_diamonds,
        ace_diamonds,
        ace_hearts,
        ace_hearts,
        ace_hearts,
        ace_hearts,
        ace_hearts,
        ace_hearts,
        ace_spades,
        ace_spades,
        ace_spades,
        ])

    assert not hand.is_bust()
