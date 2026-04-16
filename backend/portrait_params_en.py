"""
Параметры портретов randomuser для EN-демо — по **точному имени** мемориала (как в сидах).

Раньше `seed_english_portraits.py` опирался на жёсткие `memorial_id` (22, 31, …): после
`seed_english.py` на пустой БД Helen = id 10, а не 31 — портреты «жены» и «мужа»
оказывались у чужих карточек. Привязка по имени устойчива к порядку вставки.
"""

# Имя (как в Memorial.name) → { gender, age_min, age_max, nat? }
PORTRAIT_PARAMS_BY_NAME: dict[str, dict] = {
    # seed_english.py — Kelly + Anderson core
    "Sean Patrick Kelly": {"gender": "male", "age_min": 62, "age_max": 78},
    "Brigid O'Brien Kelly": {"gender": "female", "age_min": 65, "age_max": 82},
    "Thomas Michael Kelly": {"gender": "male", "age_min": 68, "age_max": 85},
    "Rose Whitfield Kelly": {"gender": "female", "age_min": 68, "age_max": 85},
    "James William Kelly": {"gender": "male", "age_min": 55, "age_max": 72},
    "Duncan Alasdair Anderson": {"gender": "male", "age_min": 62, "age_max": 80},
    "Flora Mackenzie Anderson": {"gender": "female", "age_min": 65, "age_max": 82},
    "William Duncan Anderson": {"gender": "male", "age_min": 58, "age_max": 75},
    "Agnes Brown Anderson": {"gender": "female", "age_min": 62, "age_max": 80},
    "Helen Margaret Anderson Kelly": {"gender": "female", "age_min": 62, "age_max": 80},
    "Robert James Kelly": {"gender": "male", "age_min": 52, "age_max": 70},
    "Mary Frances Kelly": {"gender": "female", "age_min": 68, "age_max": 85},
    "Patricia Anne Kelly": {"gender": "female", "age_min": 55, "age_max": 75},
    "Arthur William Anderson": {"gender": "male", "age_min": 55, "age_max": 72},
    "Linda Mei Chen Kelly": {"gender": "female", "age_min": 55, "age_max": 75},
    "Claire Ying Kelly": {"gender": "female", "age_min": 45, "age_max": 65},
    # seed_english_expanded
    "Patricia Ann Murphy Kelly": {"gender": "female", "age_min": 55, "age_max": 75},
    "Michael Robert Kelly": {"gender": "male", "age_min": 45, "age_max": 62},
    "Catherine Kelly (O'Neill)": {"gender": "female", "age_min": 45, "age_max": 65},
    "Sarah Elizabeth Kelly": {"gender": "female", "age_min": 25, "age_max": 40},
    "Daniel James Kelly": {"gender": "male", "age_min": 25, "age_max": 38},
    "George William Anderson": {"gender": "male", "age_min": 55, "age_max": 72},
    "Margaret Fraser Anderson": {"gender": "female", "age_min": 60, "age_max": 80},
    "Ian George Anderson": {"gender": "male", "age_min": 75, "age_max": 95},
    "Evelyn Parker Anderson": {"gender": "female", "age_min": 70, "age_max": 90},
    # seed_english_cluster2 — Chang / Rossi (nat)
    "Ah Fong Chang": {"gender": "male", "age_min": 55, "age_max": 75, "nat": "cn"},
    "Wei Chang": {"gender": "male", "age_min": 55, "age_max": 75, "nat": "cn"},
    "Mei Lin Wu Chang": {"gender": "female", "age_min": 55, "age_max": 75, "nat": "cn"},
    "Thomas Chang": {"gender": "male", "age_min": 55, "age_max": 75, "nat": "cn"},
    "Alice Lee Chang": {"gender": "female", "age_min": 55, "age_max": 75, "nat": "cn"},
    "Richard Chang": {"gender": "male", "age_min": 55, "age_max": 75, "nat": "cn"},
    "Grace Kim Chang": {"gender": "female", "age_min": 55, "age_max": 75, "nat": "cn"},
    "David Chang": {"gender": "male", "age_min": 30, "age_max": 50, "nat": "cn"},
    "Jennifer Park Chang": {"gender": "female", "age_min": 30, "age_max": 50, "nat": "cn"},
    "Enzo Rossi": {"gender": "male", "age_min": 55, "age_max": 75, "nat": "it"},
    "Maria Conti Rossi": {"gender": "female", "age_min": 55, "age_max": 75, "nat": "it"},
    "Antonio Rossi": {"gender": "male", "age_min": 45, "age_max": 65, "nat": "it"},
    "Giulia Moretti Rossi": {"gender": "female", "age_min": 45, "age_max": 65, "nat": "it"},
    "Marco Rossi": {"gender": "male", "age_min": 25, "age_max": 45, "nat": "it"},
    "Sofia Ferrara Rossi": {"gender": "female", "age_min": 25, "age_max": 45, "nat": "it"},
    "Emily Chang": {"gender": "female", "age_min": 25, "age_max": 40, "nat": "cn"},
    "Serena Chang": {"gender": "female", "age_min": 22, "age_max": 38, "nat": "cn"},
    "Luca Rossi": {"gender": "male", "age_min": 30, "age_max": 48, "nat": "it"},
}
