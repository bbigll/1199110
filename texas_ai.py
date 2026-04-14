#!/usr/bin/env python3
"""
一个简化版德州扑克 AI：
- 支持输入自己的两张手牌、公共牌、对手人数
- 使用蒙特卡洛模拟估算胜率
- 根据胜率给出 Fold / Call / Raise 建议
"""

from __future__ import annotations

import itertools
import random
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

RANK_STR = "23456789TJQKA"
SUIT_STR = "cdhs"  # clubs, diamonds, hearts, spades


@dataclass(frozen=True, order=True)
class Card:
    rank: int  # 2-14
    suit: str  # c,d,h,s

    def __str__(self) -> str:
        return f"{RANK_STR[self.rank - 2]}{self.suit}"


def parse_card(token: str) -> Card:
    token = token.strip().lower()
    if len(token) != 2:
        raise ValueError(f"无效牌面: {token}")
    r, s = token[0], token[1]
    if r.upper() not in RANK_STR or s not in SUIT_STR:
        raise ValueError(f"无效牌面: {token}")
    return Card(rank=RANK_STR.index(r.upper()) + 2, suit=s)


def make_deck(excluded: Iterable[Card] = ()) -> List[Card]:
    excluded_set = set(excluded)
    return [
        Card(rank=r, suit=s)
        for r in range(2, 15)
        for s in SUIT_STR
        if Card(rank=r, suit=s) not in excluded_set
    ]


def evaluate_5(cards: Sequence[Card]) -> Tuple[int, Tuple[int, ...]]:
    """返回 (牌型等级, 细分比较元组)，值越大越强。"""
    ranks = sorted((c.rank for c in cards), reverse=True)
    counts = Counter(ranks)
    count_rank = sorted(((cnt, r) for r, cnt in counts.items()), reverse=True)
    suits = [c.suit for c in cards]

    is_flush = len(set(suits)) == 1

    unique_ranks = sorted(set(ranks), reverse=True)
    is_wheel = unique_ranks == [14, 5, 4, 3, 2]
    is_straight = (
        len(unique_ranks) == 5 and unique_ranks[0] - unique_ranks[-1] == 4
    ) or is_wheel
    straight_high = 5 if is_wheel else unique_ranks[0]

    if is_straight and is_flush:
        return 8, (straight_high,)

    if count_rank[0][0] == 4:
        four = count_rank[0][1]
        kicker = max(r for r in ranks if r != four)
        return 7, (four, kicker)

    if count_rank[0][0] == 3 and count_rank[1][0] == 2:
        return 6, (count_rank[0][1], count_rank[1][1])

    if is_flush:
        return 5, tuple(ranks)

    if is_straight:
        return 4, (straight_high,)

    if count_rank[0][0] == 3:
        trips = count_rank[0][1]
        kickers = sorted((r for r in ranks if r != trips), reverse=True)
        return 3, (trips, *kickers)

    if count_rank[0][0] == 2 and count_rank[1][0] == 2:
        pair_hi = max(count_rank[0][1], count_rank[1][1])
        pair_lo = min(count_rank[0][1], count_rank[1][1])
        kicker = max(r for r in ranks if r != pair_hi and r != pair_lo)
        return 2, (pair_hi, pair_lo, kicker)

    if count_rank[0][0] == 2:
        pair = count_rank[0][1]
        kickers = sorted((r for r in ranks if r != pair), reverse=True)
        return 1, (pair, *kickers)

    return 0, tuple(ranks)


def best_hand_score(cards7: Sequence[Card]) -> Tuple[int, Tuple[int, ...]]:
    return max(evaluate_5(c) for c in itertools.combinations(cards7, 5))


def estimate_win_rate(
    hole_cards: Sequence[Card],
    board_cards: Sequence[Card],
    opponents: int = 1,
    simulations: int = 5000,
) -> float:
    if len(hole_cards) != 2:
        raise ValueError("手牌必须是 2 张")
    if len(board_cards) > 5:
        raise ValueError("公共牌最多 5 张")
    if opponents < 1:
        raise ValueError("至少 1 个对手")

    known = list(hole_cards) + list(board_cards)
    if len(set(known)) != len(known):
        raise ValueError("牌重复了，请检查输入")

    deck = make_deck(known)
    wins = 0.0

    for _ in range(simulations):
        random.shuffle(deck)

        need_board = 5 - len(board_cards)
        draw_index = 0

        sim_board = list(board_cards) + deck[draw_index : draw_index + need_board]
        draw_index += need_board

        hero_score = best_hand_score(list(hole_cards) + sim_board)

        opp_scores = []
        for _opp in range(opponents):
            opp_hole = deck[draw_index : draw_index + 2]
            draw_index += 2
            opp_scores.append(best_hand_score(opp_hole + sim_board))

        all_scores = [hero_score] + opp_scores
        best = max(all_scores)
        winners = [i for i, s in enumerate(all_scores) if s == best]

        if 0 in winners:
            wins += 1.0 / len(winners)  # 平分池

    return wins / simulations


def suggest_action(win_rate: float, pot_odds: float = 0.33) -> str:
    """
    根据胜率给建议：
    - 明显低于底池赔率：Fold
    - 接近赔率：Call
    - 显著高于赔率：Raise
    """
    if win_rate < pot_odds - 0.08:
        return "Fold"
    if win_rate > pot_odds + 0.12:
        return "Raise"
    return "Call"


def parse_cards_input(text: str) -> List[Card]:
    text = text.strip()
    if not text:
        return []
    return [parse_card(x) for x in text.split()]


def main() -> None:
    print("=== 德州扑克 AI 决策器（简化版）===")
    print("输入格式示例：As Kh（中间空格）")

    hole = parse_cards_input(input("你的两张手牌: "))
    board = parse_cards_input(input("公共牌(0~5 张，可留空): "))

    if len(hole) != 2:
        raise ValueError("你必须输入 2 张手牌")

    opponents = int(input("对手人数(默认1): ") or "1")
    sims = int(input("模拟次数(默认5000): ") or "5000")
    pot_odds = float(input("你的底池赔率(默认0.33): ") or "0.33")

    win_rate = estimate_win_rate(hole, board, opponents=opponents, simulations=sims)
    action = suggest_action(win_rate, pot_odds)

    print(f"\n估算胜率: {win_rate:.2%}")
    print(f"建议动作: {action}")


if __name__ == "__main__":
    main()
