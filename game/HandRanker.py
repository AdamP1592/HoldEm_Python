from itertools import combinations

def rank_players(community_cards, hole_cards):
    def card_value(card):
        v = card.get_value()
        if v == 1 and hasattr(card, 'high_value'):
            return card.high_value
        return v

    def score_hand(cards):
        vals = [card_value(c) for c in cards]
        vals.sort(reverse=True)
        counts = {}
        for v in vals:
            counts[v] = counts.get(v, 0) + 1
        suits = [c.suit for c in cards]
        is_flush = len(set(suits)) == 1
        uniq = sorted(set(vals), reverse=True)
        straight_high = None
        for i in range(len(uniq) - 4):
            seq = uniq[i:i+5]
            if seq[0] - seq[4] == 4:
                straight_high = seq[0]
                break
        if straight_high is None and set([14, 5, 4, 3, 2]).issubset(uniq):
            straight_high = 5
        is_straight = straight_high is not None

        if is_straight and is_flush:
            return (8, straight_high)
        items = sorted(counts.items(), key=lambda x: (-x[1], -x[0]))
        if items[0][1] == 4:
            four = items[0][0]
            kicker = max(v for v in vals if v != four)
            return (7, four, kicker)
        if items[0][1] == 3 and items[1][1] >= 2:
            return (6, items[0][0], items[1][0])
        if is_flush:
            return (5, *vals)
        if is_straight:
            return (4, straight_high)
        if items[0][1] == 3:
            three = items[0][0]
            kickers = [v for v in vals if v != three][:2]
            return (3, three, *kickers)
        if items[0][1] == 2 and items[1][1] == 2:
            high_pair, low_pair = items[0][0], items[1][0]
            kicker = max(v for v in vals if v not in (high_pair, low_pair))
            return (2, high_pair, low_pair, kicker)
        if items[0][1] == 2:
            pair = items[0][0]
            kickers = [v for v in vals if v != pair][:3]
            return (1, pair, *kickers)
        return (0, *vals[:5])

    def best_score(seven):
        best = None
        for combo in combinations(seven, 5):
            sc = score_hand(combo)
            if best is None or sc > best:
                best = sc
        return best

    scores = {
        player_key: best_score(hole + community_cards)
        for player_key, hole in hole_cards.items()
    }
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    ranked = []
    prev_score = None
    for player_key, score in sorted_scores:
        if score != prev_score:
            ranked.append([player_key])
            prev_score = score
        else:
            ranked[-1].append(player_key)
    return ranked

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
    total_cards = hand.get_cards() + community_cards


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

