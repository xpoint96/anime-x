from __future__ import annotations

import json
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "anime.json"

GENRES = [
    "фэнтези",
    "экшен",
    "сверхъестественное",
    "меха",
    "драма",
    "повседневность",
    "музыка",
    "приключения",
    "фантастика",
    "романтика",
    "комедия",
    "ужасы",
    "спорт",
    "детектив",
]

KINDS = ["TV", "ONA", "OVA", "фильм"]
SEASONS = ["весна", "лето", "осень", "зима"]
STATUSES = ["онгоинг", "анонс", "завершено"]
SORTS = {
    "new": "Новые на сайте",
    "rating": "По рейтингу",
    "title": "По названию",
    "year": "По году",
}


def build_catalog() -> list[dict]:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    items: list[dict] = []
    for index, row in enumerate(raw, start=1):
        episodes = max(1, int(row.get("episodes") or 12))
        out = min(episodes, (index * 3) % (episodes + 1))
        season = SEASONS[(index - 1) % len(SEASONS)]
        items.append(
            {
                "id": index,
                "slug": str(index),
                "anilist_id": row.get("anilist_id"),
                "title": row["title"],
                "year": int(row.get("year") or 2024),
                "kind": row.get("kind") or "TV",
                "episodes": episodes,
                "out": out,
                "rating": float(row.get("rating") or 7.0),
                "genre": row.get("genre") or "аниме",
                "tag": season,
                "status": row.get("status") or "завершено",
                "poster_url": row["poster_url"],
                "synopsis": row.get("synopsis") or "",
                "new": index <= 24,
                "updated": f"сегодня, {10 + (index % 12)}:{index % 6}0",
            }
        )
    return items


CATALOG = build_catalog()
BY_ID = {item["id"]: item for item in CATALOG}

# keep genre filter list aligned with data
_data_genres = sorted({item["genre"] for item in CATALOG})
GENRES = _data_genres or GENRES

COLLECTIONS = [
    {
        "slug": "top-ekshen",
        "title": "Топ экшен",
        "text": "Драки, клинки и сезоны, которые не дают скучать.",
        "ids": [1, 2, 3, 4, 5, 8],
    },
    {
        "slug": "klassika",
        "title": "Классика",
        "text": "Тайтлы, которые почти все уже смотрели.",
        "ids": [6, 7, 9, 10, 12, 15],
    },
    {
        "slug": "fan-meha",
        "title": "Аниме фан: меха",
        "text": "Подборка для тех, кто любит сталь и пилотов.",
        "ids": [i["id"] for i in CATALOG if i["genre"] == "меха"][:6] or [11, 16, 21, 26, 31, 36],
    },
    {
        "slug": "tihoe",
        "title": "Тихое утро",
        "text": "Повседневность и спокойные истории под пледом.",
        "ids": [i["id"] for i in CATALOG if i["genre"] == "повседневность"][:6] or [14, 18, 22, 27, 33, 40],
    },
]

REVIEWS = [
    {
        "id": 1,
        "title": CATALOG[0]["title"] if CATALOG else "Аниме",
        "anime_id": 1,
        "author": "mira",
        "score": 9,
        "text": "Темп держит до конца. Первый сезон заходит сразу.",
    },
    {
        "id": 2,
        "title": CATALOG[1]["title"] if len(CATALOG) > 1 else "Аниме",
        "anime_id": 2,
        "author": "kade",
        "score": 8,
        "text": "Боёвка и атмосфера на месте. Смотрится красиво.",
    },
    {
        "id": 3,
        "title": CATALOG[2]["title"] if len(CATALOG) > 2 else "Аниме",
        "anime_id": 3,
        "author": "sora",
        "score": 8,
        "text": "Персонажи цепляют. Хочется сразу вторую часть.",
    },
    {
        "id": 4,
        "title": CATALOG[3]["title"] if len(CATALOG) > 3 else "Аниме",
        "anime_id": 4,
        "author": "ren",
        "score": 9,
        "text": "Классика жанра. Для зимнего сезона — топ.",
    },
    {
        "id": 5,
        "title": CATALOG[4]["title"] if len(CATALOG) > 4 else "Аниме",
        "anime_id": 5,
        "author": "yui",
        "score": 8,
        "text": "Лёгкий вход, сильный вайб. Можно советовать новичкам.",
    },
    {
        "id": 6,
        "title": CATALOG[5]["title"] if len(CATALOG) > 5 else "Аниме",
        "anime_id": 6,
        "author": "leo",
        "score": 8,
        "text": "Сюжет не отпускает. Серии пролетают незаметно.",
    },
]


def apply_filters(
    items: list[dict],
    query: str = "",
    kind: str = "",
    season: str = "",
    genre: str = "",
    exclude: str = "",
    status: str = "",
    sort: str = "new",
) -> list[dict]:
    result = items
    needle = query.strip().lower()
    if needle:
        result = [
            item
            for item in result
            if needle in item["title"].lower() or needle in item["genre"].lower()
        ]
    if kind and kind != "все":
        result = [item for item in result if item["kind"] == kind]
    if season and season != "все":
        result = [item for item in result if item["tag"] == season]
    if genre and genre != "все":
        result = [item for item in result if item["genre"] == genre]
    if exclude and exclude != "нет":
        result = [item for item in result if item["genre"] != exclude]
    if status and status != "все":
        result = [item for item in result if item["status"] == status]
    if sort == "rating":
        result = sorted(result, key=lambda item: item["rating"], reverse=True)
    elif sort == "title":
        result = sorted(result, key=lambda item: item["title"])
    elif sort == "year":
        result = sorted(result, key=lambda item: item["year"], reverse=True)
    else:
        result = sorted(result, key=lambda item: item["id"])
    return result
