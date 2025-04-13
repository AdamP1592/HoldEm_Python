from itertools import combinations

def check_for_straight(cards):
    # Build a set of distinct card values.
    # For an Ace, add both its low (e.g. 1) and its high (e.g. 14) values.
    distinct = {}
    values = set()
    for card in cards:
        v = card.get_value()  # primary value
        if v not in distinct:
            distinct[v] = card
        values.add(v)
        if card.get_name().startswith("A"):
            values.add(card.high_value)
            if card.high_value not in distinct:
                distinct[card.high_value] = card
    sorted_vals = sorted(values, reverse=True)
    # Look for 5 consecutive numbers.
    for i in range(len(sorted_vals) - 4):
        seq = sorted_vals[i:i+5]
        if seq[0] - seq[4] == 4:
            # Return the sequence of cards (using the stored card for each value)
            straight_cards = [distinct[v] for v in seq]
            return straight_cards, sum(seq)
    return None, 0

def get_best_hand_value(hand, community_cards):
    total_cards = hand.get_hand() + community_cards


    # Group cards by suit.
    suit_groups = {}
    for card in total_cards:
        suit_groups.setdefault(card.suit, []).append(card)
    
    # Check for flush (and later, straight flush).
    flush_candidate = None
    flush_value = 0
    for s, group in suit_groups.items():
        if len(group) >= 5:
            sorted_group = sorted(group, key=lambda c: c.get_value(), reverse=True)
            candidate = sorted_group[:5]
            candidate_value = sum(c.get_value(True) for c in candidate)
            if candidate_value > flush_value:
                flush_candidate = candidate
                flush_value = candidate_value
    
    # Check for overall straight (using all cards).
    sorted_total = sorted(total_cards, key=lambda c: c.get_value(), reverse=True)
    straight_cards, straight_value = check_for_straight(sorted_total)
    
    # Check for straight flush (in each suit group that qualifies)
    straight_flush_candidate = None
    straight_flush_value = 0
    for s, group in suit_groups.items():
        if len(group) >= 5:
            sorted_group = sorted(group, key=lambda c: c.get_value(), reverse=True)
            sf_cards, sf_value = check_for_straight(sorted_group)
            if sf_cards is not None and sf_value > straight_flush_value:
                straight_flush_candidate = sf_cards
                straight_flush_value = sf_value

    # Highest category first.
    if straight_flush_candidate:
        # Determine if it's a Royal Straight Flush (10, J, Q, K, A).
        # We get the effective values by using high_value for Ace.
        candidate_values = sorted([c.get_value(True) if c.get_name().startswith("A") else c.get_value() for c in straight_flush_candidate], reverse=True)
        if candidate_values[:5] == [14, 13, 12, 11, 10]:
            return ("Royal Straight Flush", straight_flush_value)
        return ("Straight Flush", straight_flush_value)

    # Build a frequency dictionary for card values (using the low value for consistency).
    freq = {}
    for card in total_cards:
        card.visible = True
        v = None
        if card.get_name()[0] == "A":
            v = card.get_value(True)
        else:
            v = card.get_value()
        freq[v] = freq.get(v, 0) + 1




    # 4 of a Kind
    for val, count in freq.items():
        if count == 4:
            return ("4 of a kind", val * 4)
    
    # Full House: find a three-of-a-kind and then a pair (exclude the three-of-a-kind's value for the pair if possible)
    three_vals = sorted([val for val, count in freq.items() if count >= 3], reverse=True)
    pair_vals = sorted([val for val, count in freq.items() if count >= 2], reverse=True)
    if three_vals:
        primary_three = three_vals[0]
        # Remove the three-of-a-kind value from pair candidates if possible.
        pair_candidates = [v for v in pair_vals if v != primary_three]
        if pair_candidates:
            return ("Full House", primary_three * 3 + pair_candidates[0] * 2)
    
    # Flush (if any flush candidate exists)
    if flush_candidate is not None:
        return ("Flush", flush_value)
    
    # Straight
    if straight_cards is not None:
        return ("Straight", straight_value)
    
    # Three of a Kind
    if three_vals:
        return ("Three of a kind", three_vals[0] * 3)
    
    # Two Pair
    if len(pair_vals) >= 2:
        return ("Two Pair", pair_vals[0] * 2 + pair_vals[1] * 2)
    
    # One Pair
    if pair_vals:
        return ("Pair", pair_vals[0] * 2)
    
    # High Card
    high_card = max(total_cards, key=lambda c: c.get_value())
    return ("High Card", high_card.get_value())