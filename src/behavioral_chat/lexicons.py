"""Behaviour categories and keywords, by relationship type.

Every category is applied to BOTH people in the same way. Keywords are
plain phrases; a trailing * lets a word take suffixes (e.g. "بوس*" matches
بوس, بوسه, بوست). Persian, Finglish and English are included; anyone can add
their own keywords per category at call time.
"""
from __future__ import annotations

import re
import unicodedata

PERSIAN = "؀-ۿ"

# ------------------------------------------------------------------ normalisation
_AR2FA = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه", "أ": "ا", "إ": "ا", "آ": "ا"})
_DIACRITICS = re.compile("[ً-ْٰـ]")  # harakat, superscript alef, tatweel


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = text.translate(_AR2FA)
    text = _DIACRITICS.sub("", text)
    text = text.replace("‌", "").replace("‍", "").replace("‎", "").replace("‏", "")
    text = re.sub(r"(.)\1{2,}", r"\1", text)          # soooo -> so, جووووون -> جون
    text = re.sub(r"([اویه])\1+", r"\1", text)         # doubled Persian vowels -> single
    return text.lower()


# ------------------------------------------------------------------ categories
# group: "warm" and "tension" feed the alignment index; "neutral" is reported only.
BASE = {
    "warmth": {
        "label": "Warmth & affection", "group": "warm",
        "fa": ["عزیزم", "عزیز دلم", "جانم", "جونم", "عشقم", "عشق من", "دوستت دارم", "دوست دارم",
               "دلم برات تنگ", "دلم تنگ", "قربونت", "فدات", "عسلم", "نفسم", "ماچ", "بوس*", "خوشگلم",
               "ناز نازی", "بغل*"],
        "en": ["love you", "miss you", "my love", "dear", "darling", "honey", "babe", "baby", "sweetheart",
               "xoxo", "hug*", "kisses", "azizam", "joonam", "eshgham", "ghorboonet", "dooset daram"],
        "emoji": ["❤", "🥰", "😘", "💋", "💕", "💜", "😍", "🤗", "🌹", "♥"],
    },
    "care": {
        "label": "Care & checking in", "group": "warm",
        "fa": ["خوبی", "حالت چطوره", "حالت خوبه", "چطوری", "چه خبر", "خسته نباشی", "مواظب خودت", "مراقب خودت",
               "صبح بخیر", "صبحت بخیر", "صبحتون بخیر", "شب بخیر", "شبت بخیر", "شبتون بخیر", "خوب بخوابی",
               "رسیدی", "غذا خوردی", "بهتری", "نگرانت", "حالت بهتره"],
        "en": ["how are you", "how r u", "how was your day", "take care", "good morning", "good night",
               "sleep well", "did you eat", "are you ok", "feeling better", "get home safe", "worried about you",
               "khoobi", "chetori", "sobh bekheir", "shab bekheir"],
        "emoji": [],
    },
    "appreciation": {
        "label": "Thanks & appreciation", "group": "warm",
        "fa": ["مرسی", "ممنون*", "سپاس", "دستت درد نکنه", "لطف کردی", "عالیه", "عالی بود", "افرین", "ایول",
               "چه خوب"],
        "en": ["thanks", "thank you", "thx", "appreciate*", "great job", "well done", "awesome",
               "you're the best", "merci", "mamnoon"],
        "emoji": ["🙏"],
    },
    "requests": {
        "label": "Requests & asks", "group": "neutral",
        "fa": ["لطفا", "میشه", "میتونی", "میخوام", "بفرست", "برام بفرست", "انجام بده", "بگو ببینم"],
        "en": ["please", "can you", "could you", "would you", "i want", "send me", "let me know", "tell me"],
        "emoji": [],
    },
    "refusals": {
        "label": "Refusals & boundaries", "group": "tension",
        "fa": ["نمیخوام", "نمیتونم", "نمیدم", "نمیفرستم", "نمیفرسم", "بسه", "کافیه", "تمومش کن", "شیطون نشو",
               "دوست ندارم", "راحت نیستم", "خط قرمز", "حریم", "اجازه نمیدم", "عمرا", "ولم کن", "گیر نده",
               "زشته", "بی ادب نشو", "نه مرسی", "نه نمیخوام", "اصلا نمیخوام"],
        "en": ["no thanks", "i don't want", "i dont want", "i can't", "stop it", "please stop", "that's enough",
               "not comfortable", "please don't", "don't do that", "boundar*", "leave me alone", "back off",
               "not okay", "not ok with"],
        "emoji": [],
    },
    "labeling": {
        "label": "Labeling or dismissing the other", "group": "tension",
        "fa": ["بی ادب", "بی جنبه", "جنبه نداری", "دیوونه", "کس خل", "کسخل", "خل شدی", "احمق", "متعصب", "تعصب",
               "عقب افتاده", "حساسی", "زیادی حساس", "زیادی فکر", "اورتینک*", "شوخی بود", "شوخی کردم", "جدی نگیر",
               "بزرگش نکن", "شلوغش نکن", "گیر میدی", "گیر دادی", "پررو", "لوس", "بچه ای", "تابو", "دیکتاتور*",
               "تو همیشه", "تو هیچوقت"],
        "en": ["you're crazy", "youre crazy", "overreact*", "too sensitive", "overthink*", "just a joke",
               "calm down", "drama", "stupid", "idiot", "you always", "you never", "rude", "immature", "whatever"],
        "emoji": ["🙄"],
    },
    "apology": {
        "label": "Apology & repair", "group": "warm",
        "fa": ["ببخشید", "ببخش", "معذرت", "شرمنده", "حق با توئه", "حق داری", "اشتباه کردم", "منظوری نداشتم"],
        "en": ["sorry", "my bad", "apologi*", "you're right", "i was wrong", "didn't mean"],
        "emoji": [],
    },
    "plans": {
        "label": "Plans & invitations", "group": "neutral",
        "fa": ["بریم", "همو ببینیم", "ببینمت", "قرار بذاریم", "اخر هفته", "کی میای", "بیام پیشت", "بیا پیشم",
               "کافه", "شام بریم"],
        "en": ["let's meet", "lets meet", "see you", "wanna meet", "want to meet", "this weekend", "dinner",
               "coffee", "let's go", "come over", "make a plan"],
        "emoji": [],
    },
    "endings": {
        "label": "Endings & withdrawal", "group": "tension",
        "fa": ["خداحافظ", "خدافظ", "بدرود", "دیگه پیام نده", "دیگه حرف نزنیم", "با من حرف نزن", "تمومش کنیم",
               "همینجا تموم", "موو ان", "مووان", "تایم ایز اوور"],
        "en": ["goodbye", "we're done", "were done", "it's over", "don't text me", "don't message me",
               "move on", "time is over"],
        "emoji": ["👋"],
    },
}

EXTRA = {
    "sexual": {
        "label": "Sexual or body-focused", "group": "neutral",
        "fa": ["سکس*", "لخت", "نیکید", "برهنه", "سینه*", "نیپل*", "باسن", "کون*", "کس", "کست", "شورت*", "سوتین",
               "لباس زیر", "بیکینی", "هات", "حشری", "هورنی", "بدنت", "اندامت", "لبات", "گردنت", "رابطه جنسی"],
        "en": ["sex*", "naked", "nude*", "boobs", "breast*", "nipple*", "ass", "butt", "horny", "lingerie",
               "bikini", "hot pic*", "turn me on", "your body"],
        "emoji": ["🍑", "🍆", "💦", "😈"],
    },
    "see_request": {
        "label": "Requests to see / hear", "group": "neutral",
        "fa": ["عکس بده", "عکس بفرست", "عکس داری", "عکستو", "ویدیو بفرست", "ویدیو بده", "ویس بده", "ویس بفرست",
               "ویدیو کال", "ویدیوکال", "کال کن", "زنگ بزن", "فیس تایم", "نشونم بده", "عکس هات"],
        "en": ["send a pic", "send pic*", "send me a photo", "pic of you", "video call", "facetime", "call me",
               "voice note", "show me", "let me see"],
        "emoji": [],
    },
    "commitment": {
        "label": "Future & commitment talk", "group": "warm",
        "fa": ["اینده", "ازدواج", "با هم زندگی", "رابطه جدی", "هدفت چیه", "انتظارت چیه", "تعهد", "دوست دختر",
               "دوست پسر", "پارتنر"],
        "en": ["future", "marry", "marriage", "serious relationship", "exclusive", "girlfriend", "boyfriend",
               "commitment", "what are we", "what do you want from this"],
        "emoji": [],
    },
    "checking_up": {
        "label": "Jealousy & checking up", "group": "tension",
        "fa": ["با کی بودی", "کجا بودی", "کی بود", "حسودی*", "چرا جواب ندادی", "انلاین بودی", "چرا سین کردی"],
        "en": ["who were you with", "where were you", "jealous", "why didn't you reply", "you were online",
               "left me on read"],
        "emoji": [],
    },
    "support": {
        "label": "Support & encouragement", "group": "warm",
        "fa": ["نگران نباش", "درست میشه", "از پسش برمیای", "کنارتم", "هستم برات", "هر کاری داشتی", "بهت افتخار"],
        "en": ["don't worry", "you got this", "i'm here for you", "proud of you", "it'll be ok", "here if you need"],
        "emoji": ["💪"],
    },
    "humor": {
        "label": "Humor & play", "group": "warm",
        "fa": ["خخخ", "خخ", "ههه", "جوک", "شوخی"],
        "en": ["lol", "lmao", "haha*", "hehe"],
        "emoji": ["😂", "🤣", "😆", "😜"],
    },
    "obligation": {
        "label": "Obligation & guilt", "group": "tension",
        "fa": ["وظیفته", "چرا زنگ نزدی", "سر نمیزنی", "یادی از ما", "بعد اینهمه", "به فکر ما نیستی", "باید بیای"],
        "en": ["you should", "why didn't you call", "you never visit", "after all we've done", "you owe"],
        "emoji": [],
    },
    "tasks": {
        "label": "Tasks & deadlines", "group": "neutral",
        "fa": ["ددلاین", "مهلت", "فوری", "تا فردا", "گزارش", "جلسه", "پروژه", "تسک", "ایمیل"],
        "en": ["deadline", "asap", "urgent", "eod", "report", "meeting", "project", "task", "by tomorrow"],
        "emoji": [],
    },
    "blame": {
        "label": "Blame & criticism", "group": "tension",
        "fa": ["اشتباه کردی", "تقصیر", "چرا انجام ندادی", "قابل قبول نیست", "دوباره انجام بده", "ایراد داره"],
        "en": ["your fault", "you didn't", "unacceptable", "mistake", "redo", "why didn't you"],
        "emoji": [],
    },
}

TYPES = {
    "romantic": {
        "label": "Romantic / dating",
        "categories": ["warmth", "care", "appreciation", "commitment", "plans", "requests", "see_request",
                       "sexual", "refusals", "labeling", "checking_up", "apology", "endings"],
    },
    "friendship": {
        "label": "Friendship",
        "categories": ["warmth", "care", "support", "humor", "appreciation", "plans", "requests", "refusals",
                       "labeling", "apology", "endings"],
    },
    "family": {
        "label": "Family",
        "categories": ["warmth", "care", "support", "appreciation", "plans", "requests", "obligation", "refusals",
                       "labeling", "apology", "endings"],
    },
    "work": {
        "label": "Work / professional",
        "categories": ["appreciation", "care", "tasks", "requests", "refusals", "blame", "labeling", "apology",
                       "plans"],
    },
    "other": {
        "label": "Other",
        "categories": ["warmth", "care", "appreciation", "plans", "requests", "refusals", "labeling", "apology",
                       "endings"],
    },
}

ALL = {**BASE, **EXTRA}


def _compile(phrase: str) -> re.Pattern:
    star = phrase.endswith("*")
    p = normalize(phrase.rstrip("*"))
    body = re.escape(p).replace(r"\ ", r"\s+")
    is_fa = bool(re.search(f"[{PERSIAN}]", p))
    if is_fa:
        left, right = f"(?<![{PERSIAN}])", "" if star else f"(?![{PERSIAN}])"
    else:
        left, right = r"(?<![a-z])", "" if star else r"(?![a-z])"
    return re.compile(left + body + right)


ALIASES = {"love": "romantic", "dating": "romantic", "friends": "friendship", "friend": "friendship",
           "colleagues": "work", "colleague": "work", "professional": "work", "families": "family"}


def resolve_type(relationship_type: str | None) -> str:
    rt = (relationship_type or "other").strip().lower()
    rt = ALIASES.get(rt, rt)
    return rt if rt in TYPES else "other"


def build(relationship_type: str, extra_keywords: dict[str, list[str]] | None = None) -> dict:
    """Return {category: {"label", "group", "patterns": [...], "keywords": [...]}} for one relationship type."""
    rt = resolve_type(relationship_type)
    out = {}
    for cat in TYPES[rt]["categories"]:
        spec = ALL[cat]
        words = spec["fa"] + spec["en"]
        out[cat] = {
            "label": spec["label"],
            "group": spec["group"],
            "keywords": words + spec["emoji"],
            "patterns": [_compile(w) for w in words],
            "emoji": list(spec["emoji"]),
        }
    for cat, words in (extra_keywords or {}).items():
        words = [w for w in words if isinstance(w, str) and w.strip()][:200]
        if cat not in out:
            base = ALL.get(cat, {"label": cat.replace("_", " ").capitalize(), "group": "neutral"})
            out[cat] = {"label": base["label"], "group": base["group"], "keywords": [], "patterns": [], "emoji": []}
        out[cat]["keywords"] += words
        out[cat]["patterns"] += [_compile(w) for w in words if re.search(r"\w", w)]
        out[cat]["emoji"] += [w for w in words if not re.search(r"\w", w)]
    return out


def describe() -> dict:
    """Plain description of every relationship type and its categories (for transparency)."""
    return {
        rt: {
            "label": spec["label"],
            "categories": {
                c: {"label": ALL[c]["label"], "group": ALL[c]["group"],
                    "keywords": ALL[c]["fa"] + ALL[c]["en"] + ALL[c]["emoji"]}
                for c in spec["categories"]
            },
        }
        for rt, spec in TYPES.items()
    }
