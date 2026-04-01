"""
Канонический набор английских демо-мемориалов (инвестор / демо).
Счёт и имена должны совпадать с цепочкой сидов:
  seed_english.py → seed_english_expanded.py → seed_english_cluster2.py

Итого: 43 уникальных записей с language='en'.
"""

EXPECTED_EN_COUNT = 43

# Все имена в точности как в сидах (для проверок и документации).
EXPECTED_EN_NAMES = frozenset(
    {
        # seed_english.py (11)
        "Sean Patrick Kelly",
        "Brigid O'Brien Kelly",
        "Thomas Michael Kelly",
        "Rose Whitfield Kelly",
        "James William Kelly",
        "Duncan Alasdair Anderson",
        "Flora Mackenzie Anderson",
        "William Duncan Anderson",
        "Agnes Brown Anderson",
        "Helen Margaret Anderson Kelly",
        "Robert James Kelly",
        # seed_english.py — доп. персонажи (siblings / Gen 4–5), не входили в старый подсчёт «11»
        "Mary Frances Kelly",
        "Patricia Anne Kelly",
        "Arthur William Anderson",
        "Linda Mei Chen Kelly",
        "Claire Ying Kelly",
        # seed_english_expanded.py (+9 → 25)
        "Patricia Ann Murphy Kelly",
        "Michael Robert Kelly",
        "Catherine Kelly (O'Neill)",
        "Sarah Elizabeth Kelly",
        "Daniel James Kelly",
        "George William Anderson",
        "Margaret Fraser Anderson",
        "Ian George Anderson",
        "Evelyn Parker Anderson",
        # seed_english_cluster2.py (+18 → 43)
        "Ah Fong Chang",
        "Wei Chang",
        "Mei Lin Wu Chang",
        "Thomas Chang",
        "Alice Lee Chang",
        "Richard Chang",
        "Grace Kim Chang",
        "David Chang",
        "Jennifer Park Chang",
        "Enzo Rossi",
        "Maria Conti Rossi",
        "Antonio Rossi",
        "Giulia Moretti Rossi",
        "Marco Rossi",
        "Sofia Ferrara Rossi",
        # seed_english_cluster2.py — дочери Chang + Luca Rossi (младший брат Marco)
        "Emily Chang",
        "Serena Chang",
        "Luca Rossi",
    }
)

assert len(EXPECTED_EN_NAMES) == EXPECTED_EN_COUNT, "Manifest must list exactly EXPECTED_EN_COUNT names"
