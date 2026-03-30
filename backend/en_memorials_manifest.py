"""
Канонический набор английских демо-мемориалов (инвестор / демо).
Счёт и имена должны совпадать с цепочкой сидов:
  seed_english.py → seed_english_expanded.py → seed_english_cluster2.py

Итого: 35 уникальных записей с language='en'.
"""

EXPECTED_EN_COUNT = 35

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
        # seed_english_expanded.py (+9 → 20)
        "Patricia Ann Murphy Kelly",
        "Michael Robert Kelly",
        "Catherine O'Neill Kelly",
        "Sarah Elizabeth Kelly",
        "Daniel James Kelly",
        "George William Anderson",
        "Margaret Fraser Anderson",
        "Ian George Anderson",
        "Evelyn Parker Anderson",
        # seed_english_cluster2.py (+15 → 35)
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
    }
)

assert len(EXPECTED_EN_NAMES) == EXPECTED_EN_COUNT, "Manifest must list exactly 35 names"
