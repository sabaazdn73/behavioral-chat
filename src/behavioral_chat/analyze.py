"""Symmetric behaviour analysis of a two-person chat.

Every metric is computed for both people in the same way. The output is
plain JSON: counts, weekly and daily series, reply speed, alignment and
balance indices, a simple volume trend, emerging words and a few short
example messages per category, so an assistant can interpret the
pattern with evidence on both sides.
"""
from __future__ import annotations

import math
import re
import statistics as st
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from . import lexicons
from .parsers import Message

STOPWORDS = set(
    """
من تو او ما شما اون این ان که و به از در با را رو هم یه یک چی چه نه اره بله باشه خب خو دیگه هست هس نیست
نیس بود میشه شد کن کنی کنم کرد کردم کردی میکنی میکنم میکنه داره دارم داری ولی اما اگه یا تا برا برای واسه
همین همون اینو اونو چرا کجا کی چطور چجوری چند هر همه خیلی یکم کم زیاد بعد قبل الان حالا فقط هیچی هیچ
چیز چیزی یعنی مگه اصا اصلا بابا اقا اهان اوهوم واقعا راسی پس دقیقا البته کلا شاید باید نباید میخوام میخوای
میدونم نمیدونم بگو بگی بگم گفتم گفتی میگم میگی جا ام ای ها بی کرده شده بشه بشی باش باشی بده بدی بدم میدی
میدم منم توام اینم اونم بهت بهم ازت ازم باهات باهام برات برام دیگ همش خودم خودت خودش هستم هستی هستیم
بت کنه رفتی رفته رفتم دیدی دیدم تازه نگاه جای باهم نظر معلوم نگه ربطی بخدا قاطی کنیم کنید کنن شده بودم بودی
میاد میای میام اومد اومدی اومدم دارن داریم میره میرم میری بیا برو بزن زد زدی زدم خوبه بده بدی چیه کیه کجاست
the a an and or but to of in on at for with is are was were be been it this that i you he she we they me my
your his her our their so not no yes ok okay just do did does have has had will would can could what when
where why how if then than too very im its it's i'm you're dont don't u r
""".split()
)


def _week_index(ts: datetime, start: datetime) -> int:
    return (ts.date() - start.date()).days // 7


def _pearson(a: list[float], b: list[float]) -> float | None:
    if len(a) < 5 or len(set(a)) < 2 or len(set(b)) < 2:
        return None
    try:
        return st.correlation(a, b)
    except st.StatisticsError:
        return None


def _exp_trend(per_day: list[float], weeks_ahead: int = 4) -> dict:
    pts = [(i, v) for i, v in enumerate(per_day) if v > 0]
    if len(pts) < 3:
        return {"weekly_factor": None, "projection": []}
    xs, ys = zip(*[(i, math.log(v)) for i, v in pts])
    mx, my = st.mean(xs), st.mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0
    a = my - b * mx
    n = len(per_day)
    proj = [round(math.exp(a + b * (n + k)), 1) for k in range(weeks_ahead)]
    return {"weekly_factor": round(math.exp(b), 3), "projection": proj}


def _tokens(text: str) -> list[str]:
    t = lexicons.normalize(text)
    return [w for w in re.findall(r"[؀-ۿa-z]+", t) if len(w) > 1 and w not in STOPWORDS]


def pick_participants(messages: list[Message], participants: list[str] | None = None) -> list[str]:
    counts = Counter(m.sender for m in messages)
    if participants:
        names = []
        for p in participants:
            match = [s for s in counts if s.strip().lower() == p.strip().lower()]
            if not match:
                raise ValueError(f"No sender named {p!r}. Senders: {list(counts)[:20]}")
            names.append(match[0])
        if len(names) != 2:
            raise ValueError("Give exactly two participants.")
        return names
    top = [s for s, _ in counts.most_common(2)]
    if len(top) < 2:
        raise ValueError("Need messages from two people.")
    return top


def analyze(
    messages: list[Message],
    relationship_type: str = "romantic",
    participants: list[str] | None = None,
    extra_keywords: dict[str, list[str]] | None = None,
    slow_reply_minutes: int = 60,
    silence_hours: float = 3.0,
    examples_per_category: int = 2,
    include_daily: bool = True,
) -> dict:
    if not messages:
        raise ValueError("No messages to analyze.")
    messages = sorted(messages, key=lambda m: m.ts)
    A, B = pick_participants(messages, participants)
    msgs = [m for m in messages if m.sender in (A, B)]
    others = len(messages) - len(msgs)
    cats = lexicons.build(relationship_type, extra_keywords)
    start, end = msgs[0].ts, msgs[-1].ts
    n_days = (end.date() - start.date()).days + 1
    n_weeks = (n_days + 6) // 7
    day_keys = [(start.date() + timedelta(days=i)).isoformat() for i in range(n_days)]
    days_in_week = [min(7, n_days - 7 * w) for w in range(n_weeks)]

    people = (A, B)
    tot = {p: Counter() for p in people}
    weekly = {p: defaultdict(lambda: [0] * n_weeks) for p in people}
    daily = {p: defaultdict(lambda: [0] * n_days) for p in people}
    examples = {p: defaultdict(list) for p in people}
    first_use = {p: {} for p in people}
    reply_gaps = {p: [] for p in people}
    reply_gaps_w = {p: [[] for _ in range(n_weeks)] for p in people}
    words = {p: [Counter() for _ in range(n_weeks)] for p in people}
    word_first = {p: {} for p in people}

    prev = None
    for m in msgs:
        p = m.sender
        w = _week_index(m.ts, start)
        di = (m.ts.date() - start.date()).days
        norm = lexicons.normalize(m.text)
        t = tot[p]
        t["messages"] += 1
        t["characters"] += len(m.text)
        q = m.text.count("?") + m.text.count("؟")
        t["questions"] += q
        weekly[p]["messages"][w] += 1
        weekly[p]["questions"][w] += q
        daily[p]["messages"][di] += 1
        if m.media:
            t["media_" + m.media] += 1
            t["media_total"] += 1
            weekly[p]["media"][w] += 1
        if m.timed:
            t["media_timed"] += 1
        if m.ts.weekday() >= 5 or m.ts.hour < 8 or m.ts.hour >= 20:
            t["off_hours"] += 1
        if prev is not None:
            gap = (m.ts - prev.ts).total_seconds() / 60
            if gap >= silence_hours * 60:
                t["restarts_after_silence"] += 1
            if prev.sender != p and gap <= 24 * 60:
                reply_gaps[p].append(gap)
                reply_gaps_w[p][w].append(gap)
        prev = m
        hits = {
            cat for cat, spec in cats.items()
            if any(rx.search(norm) for rx in spec["patterns"]) or any(e in m.text for e in spec["emoji"])
        }
        # A message that sets a boundary *about* sexual content or photos is a boundary, not sexual content.
        if "refusals" in hits:
            hits -= {"sexual", "see_request"}
        for cat in cats:
            if cat in hits:
                t[cat] += 1
                weekly[p][cat][w] += 1
                daily[p][cat][di] += 1
                first_use[p].setdefault(cat, m.ts.date().isoformat())
                if len(examples[p][cat]) < examples_per_category and m.text.strip():
                    snippet = m.text.strip().replace("\n", " ")
                    examples[p][cat].append(
                        {"date": m.ts.date().isoformat(), "text": snippet[:90] + ("…" if len(snippet) > 90 else "")}
                    )
        for tok in _tokens(m.text):
            words[p][w][tok] += 1
            word_first[p].setdefault(tok, m.ts.date().isoformat())

    # ---------------------------------------------------------------- per-person summaries
    totals = {}
    weekly_out = {"labels": [], "days_in_week": days_in_week}
    for i in range(n_weeks):
        a = start.date() + timedelta(days=7 * i)
        b = min(end.date(), a + timedelta(days=6))
        weekly_out["labels"].append(f"W{i + 1} {a.strftime('%b %d')}–{b.strftime('%b %d')}")
    for p in people:
        g = reply_gaps[p]
        t = dict(tot[p])
        t["reply_median_minutes"] = round(st.median(g), 1) if g else None
        t["slow_reply_pct"] = round(100 * sum(1 for x in g if x > slow_reply_minutes) / len(g), 1) if g else None
        t["off_hours_pct"] = round(100 * t.get("off_hours", 0) / max(1, t["messages"]), 1)
        totals[p] = t
        per_day = [round(c / d, 1) for c, d in zip(weekly[p]["messages"], days_in_week)]
        wk = {"messages_per_day": per_day}
        for k in ["questions", "media", *cats.keys()]:
            wk[k] = list(weekly[p][k])
        wk["reply_median_minutes"] = [round(st.median(x), 1) if x else None for x in reply_gaps_w[p]]
        wk["slow_reply_pct"] = [
            round(100 * sum(1 for y in x if y > slow_reply_minutes) / len(x)) if x else None for x in reply_gaps_w[p]
        ]
        weekly_out[p] = wk

    # ---------------------------------------------------------------- joint indices
    warm = [c for c, s in cats.items() if s["group"] == "warm"]
    tense = [c for c, s in cats.items() if s["group"] == "tension"]
    align, balance = [], []
    for i in range(n_weeks):
        w_ = sum(weekly[p][c][i] for p in people for c in warm)
        t_ = sum(weekly[p][c][i] for p in people for c in tense)
        align.append(round(100 * w_ / (w_ + t_)) if (w_ + t_) else None)
        ratios = []
        for key in ("messages", "questions"):
            x, y = weekly[A][key][i], weekly[B][key][i]
            if max(x, y):
                ratios.append(min(x, y) / max(x, y))
        x = sum(weekly[A][c][i] for c in warm)
        y = sum(weekly[B][c][i] for c in warm)
        if max(x, y):
            ratios.append(min(x, y) / max(x, y))
        balance.append(round(100 * st.mean(ratios)) if ratios else None)
    weekly_out["alignment"] = align
    weekly_out["balance"] = balance

    def _mean(vals):
        vals = [v for v in vals if v is not None]
        return round(st.mean(vals)) if vals else None

    w_recent = sum(weekly[p][c][i] for p in people for c in warm for i in range(max(0, n_weeks - 3), n_weeks))
    t_recent = sum(weekly[p][c][i] for p in people for c in tense for i in range(max(0, n_weeks - 3), n_weeks))
    scenarios = {
        "same_pattern": _mean(align[-3:]),
        "early_pattern_returns": _mean(align[:3]),
        "tension_drops_80pct": round(100 * w_recent / (w_recent + 0.2 * t_recent)) if (w_recent + t_recent) else None,
        "note": "Scenario levels for the alignment index, not predictions.",
    }
    trend = {p: _exp_trend(weekly_out[p]["messages_per_day"]) for p in people}

    # ---------------------------------------------------------------- cross-person correlations (daily)
    corr = []
    series = ["messages", *cats.keys()]
    for ca in series:
        for cb in series:
            r = _pearson(daily[A][ca], daily[B][cb])
            if r is not None and abs(r) >= 0.4:
                corr.append({"a": f"{A}: {ca}", "b": f"{B}: {cb}", "r": round(r, 2)})
    own = []
    for p in people:
        for ca in series:
            for cb in series:
                if ca < cb:
                    r = _pearson(daily[p][ca], daily[p][cb])
                    if r is not None and abs(r) >= 0.5:
                        own.append({"person": p, "a": ca, "b": cb, "r": round(r, 2)})
    corr.sort(key=lambda d: -abs(d["r"]))
    own.sort(key=lambda d: -abs(d["r"]))

    # ---------------------------------------------------------------- emerging words
    emerging = {}
    week1_any = set(words[A][0]) | set(words[B][0]) if n_weeks else set()
    for p in people:
        total = Counter()
        for c in words[p]:
            total.update(c)
        rows = []
        for tok, n in total.items():
            wk = [words[p][i][tok] for i in range(n_weeks)]
            first_w = next(i for i, v in enumerate(wk) if v)
            # new to the conversation (nobody used it in week 1), used at least 3 times, not a tiny word
            if n >= 3 and first_w >= 1 and tok not in week1_any and len(tok) >= 3:
                rows.append({"word": tok, "first_seen": word_first[p][tok], "weekly": wk, "total": n})
        rows.sort(key=lambda r: (-r["total"], r["first_seen"]))
        emerging[p] = rows[:15]

    out = {
        "meta": {
            "participants": [A, B],
            "relationship_type": lexicons.resolve_type(relationship_type),
            "start": start.isoformat(timespec="minutes"),
            "end": end.isoformat(timespec="minutes"),
            "days": n_days,
            "weeks": n_weeks,
            "messages_analyzed": len(msgs),
            "messages_from_others_ignored": others,
            "categories": {c: {"label": s["label"], "group": s["group"]} for c, s in cats.items()},
            "settings": {"slow_reply_minutes": slow_reply_minutes, "silence_hours": silence_hours},
        },
        "totals": totals,
        "weekly": weekly_out,
        "trend": trend,
        "scenarios": scenarios,
        "correlations_between_people": corr[:10],
        "correlations_within_person": own[:10],
        "category_first_use": first_use,
        "emerging_words": emerging,
        "examples": {p: dict(examples[p]) for p in people},
        "method": {
            "matching": "Keyword and emoji matching after normalizing Persian/Arabic letters, diacritics, "
                        "zero-width joiners and repeated letters. One message counts once per category.",
            "alignment": "Weekly share of warm messages (warm-group categories, both people) out of warm plus "
                         "tension messages (tension-group categories, both people). 0-100.",
            "balance": "Weekly mean of min/max ratios between the two people for messages, questions and warm "
                       "messages. 100 = perfectly even.",
            "trend": "Exponential fit of messages per day per week; weekly_factor < 1 means shrinking volume.",
            "limits": "Keyword matching misses sarcasm, context and media content. Treat results as evidence "
                      "for hypotheses, never as a diagnosis of either person.",
        },
    }
    if include_daily and n_days <= 120:
        out["daily"] = {
            "labels": day_keys,
            A: {k: list(v) for k, v in daily[A].items()},
            B: {k: list(v) for k, v in daily[B].items()},
        }
    return out
