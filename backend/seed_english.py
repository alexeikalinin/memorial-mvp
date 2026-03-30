"""
Seed script: Australian memorial families (EN) for investor demo — part 1 of 3 (11 memorials).

Полный английский набор — **35** мемориалов: запускайте `seed_english_all.py` (он вызывает
`seed_english.py` → `seed_english_expanded.py` → `seed_english_cluster2.py`).
См. `en_memorials_manifest.py` — канонический список имён.

Two families across 4 generations with a cross-family marriage.

Family 1 – Kelly (Irish-Australian):
  Sean Kelly (1842-1918) + Brigid O'Brien Kelly (1848-1922)
  → Thomas Kelly (1870-1945) + Rose Whitfield Kelly (1875-1952)
    → James Kelly (1898-1968) + Helen Anderson Kelly (1895-1975)  ← cross-family
      → Robert Kelly (1930-2005)

Family 2 – Anderson (Scottish-Australian):
  Duncan Anderson (1838-1910) + Flora Mackenzie Anderson (1842-1918)
  → William Anderson (1865-1935) + Agnes Brown Anderson (1870-1940)
    → Helen Anderson (1895-1975)  ← marries James Kelly

Run from backend/ (только эта часть — 11 записей):
    source .venv/bin/activate && python seed_english.py

After full 35 seed, portrait covers (optional):
    python seed_english_portraits.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from datetime import datetime, timezone
from app.db import SessionLocal, engine
from app.models import Base, Memorial, Memory, FamilyRelationship, RelationshipType, MemorialAccess, User, UserRole
from app.services.ai_tasks import get_embedding, upsert_memory_embedding

# ── Ensure tables exist ───────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)


def dt(year, month=1, day=1):
    return datetime(year, month, day, tzinfo=timezone.utc)


# ── Memorial definitions ──────────────────────────────────────────────────────
MEMORIALS = [
    # Kelly family – Gen 1
    {
        "key": "sean",
        "name": "Sean Patrick Kelly",
        "birth": dt(1842, 3, 17),
        "death": dt(1918, 11, 4),
        "voice_gender": "male",
        "desc": "Irish-born gold miner who arrived in Victoria in 1865 and built a new life for his family in the Australian bush.",
    },
    {
        "key": "brigid",
        "name": "Brigid O'Brien Kelly",
        "birth": dt(1848, 5, 12),
        "death": dt(1922, 2, 8),
        "voice_gender": "female",
        "desc": "Born in County Cork, Ireland. Joined her husband Sean in Melbourne in 1871 and raised five children in Ballarat.",
    },
    # Kelly family – Gen 2
    {
        "key": "thomas",
        "name": "Thomas Michael Kelly",
        "birth": dt(1870, 9, 3),
        "death": dt(1945, 6, 20),
        "voice_gender": "male",
        "desc": "Eldest son of Sean and Brigid Kelly. Built a successful grocery business in Melbourne after the gold rush era.",
    },
    {
        "key": "rose",
        "name": "Rose Whitfield Kelly",
        "birth": dt(1875, 12, 15),
        "death": dt(1952, 4, 3),
        "voice_gender": "female",
        "desc": "English-Australian born in Adelaide. Married Thomas Kelly in 1896 and was the heart of their Melbourne household.",
    },
    # Kelly family – Gen 3
    {
        "key": "james",
        "name": "James William Kelly",
        "birth": dt(1898, 7, 25),
        "death": dt(1968, 10, 15),
        "voice_gender": "male",
        "desc": "RAAF pilot in World War II, Pacific theatre. Flew Kittyhawks over New Guinea. Returned to Brisbane after the war.",
    },
    # Anderson family – Gen 1
    {
        "key": "duncan",
        "name": "Duncan Alasdair Anderson",
        "birth": dt(1838, 8, 6),
        "death": dt(1910, 3, 22),
        "voice_gender": "male",
        "desc": "Scottish free settler who arrived in Adelaide in 1862. Established a sheep station in the South Australian outback.",
    },
    {
        "key": "flora",
        "name": "Flora Mackenzie Anderson",
        "birth": dt(1842, 4, 30),
        "death": dt(1918, 9, 14),
        "voice_gender": "female",
        "desc": "Born in Inverness, Scotland. Managed the Anderson homestead while Duncan worked the land. Known for her herb garden.",
    },
    # Anderson family – Gen 2
    {
        "key": "william",
        "name": "William Duncan Anderson",
        "birth": dt(1865, 11, 9),
        "death": dt(1935, 5, 17),
        "voice_gender": "male",
        "desc": "Son of Duncan and Flora. Left the family sheep station for Sydney Harbour, where he worked as a foreman during construction of the wharves.",
    },
    {
        "key": "agnes",
        "name": "Agnes Brown Anderson",
        "birth": dt(1870, 2, 21),
        "death": dt(1940, 8, 6),
        "voice_gender": "female",
        "desc": "Trained nurse at Royal Prince Alfred Hospital, Sydney. One of the first women to manage a hospital ward in NSW.",
    },
    # Cross-family – Gen 3 (Anderson daughter, marries James Kelly)
    {
        "key": "helen",
        "name": "Helen Margaret Anderson Kelly",
        "birth": dt(1895, 6, 3),
        "death": dt(1975, 1, 18),
        "voice_gender": "female",
        "desc": "Daughter of William and Agnes Anderson. Met James Kelly at a Sydney Town Hall dance in 1919 and married him the following year.",
    },
    # Kelly Gen 4
    {
        "key": "robert",
        "name": "Robert James Kelly",
        "birth": dt(1930, 4, 11),
        "death": dt(2005, 9, 30),
        "voice_gender": "male",
        "desc": "Son of James and Helen Kelly. Sydney property developer who witnessed the postwar boom and the building of the Opera House.",
    },
]

# ── Memories ──────────────────────────────────────────────────────────────────
MEMORIES = {
    "sean": [
        (
            "Leaving Cork",
            "I was twenty-three years old when I boarded the SS Great Britain in Cork Harbour. "
            "The docks smelled of salt and coal smoke. My mother pressed a Claddagh ring into my palm "
            "and told me to keep Ireland in my heart. The voyage took eleven weeks — I arrived in Melbourne "
            "in January 1865, thin and hopeful, with sixpence and a pickaxe handle to my name.",
        ),
        (
            "The Ballarat goldfields",
            "The tent city at Eureka stretched for miles when I got there. Most of the easy gold "
            "was gone, but a man with a strong back and patience could still find colour in the creek beds. "
            "I worked a claim with two Cornishmen and a Chinese fellow named Ah Fong who taught me to pan "
            "in silence. We never struck it rich, but I saved enough to buy a small block in Footscray.",
        ),
        (
            "Building the house in Footscray",
            "I built our weatherboard house myself over three summers. The timber came from Daylesford "
            "and every nail cost a penny. When Brigid arrived from Cork in 1871, she walked through the "
            "front door, looked at the bare iron roof and the dirt floor, and laughed. "
            "'It's a palace,' she said. She always had more courage than me.",
        ),
        (
            "Federation Day, 1901",
            "On the first of January 1901 the whole colony came alive. I took Thomas and the little "
            "ones to the Melbourne Town Hall where they read out the proclamation of the Commonwealth. "
            "I had been on Australian soil for thirty-six years by then. I wept — I could not help it. "
            "This was my country now, more than Ireland ever was.",
        ),
        (
            "The drought years",
            "In the dry years of the 1890s the paddocks turned to dust and the creeks ran white. "
            "We kept a vegetable garden alive with buckets from the well. Brigid bartered bread for eggs "
            "with the neighbours. I have never forgotten what real hunger feels like, and I never wasted "
            "a scrap of food for the rest of my life.",
        ),
    ],
    "brigid": [
        (
            "The voyage from Cork",
            "I was twenty-three when I sailed to join Sean. Eleven weeks on the ocean with two hundred "
            "other souls packed below decks. I learned to love the smell of rain on the sea and to "
            "hate biscuit weevils. When we sailed into Port Phillip Bay, I thought it was the most "
            "beautiful place on earth — blue water, golden hills, and no rain for months.",
        ),
        (
            "Raising five children in Ballarat",
            "Thomas was born in our Footscray house; the others followed quickly. I kept a kitchen "
            "garden and made all the children's clothes from flour sacks and remnant cotton. "
            "The school was a mile and a half away and they walked it barefoot in summer. "
            "I was harder on them than Sean — I had to be. Kindness alone does not put shoes on children.",
        ),
        (
            "The Irish community in Melbourne",
            "Every Sunday after mass we gathered at the Kellys' — a different family from us — "
            "for soda bread and gossip. The women shared recipes and the men argued about Parnell "
            "and home rule. I loved those afternoons. We kept Ireland alive in our kitchens "
            "long after we had stopped expecting to return.",
        ),
        (
            "Sean's last years",
            "When Sean's lungs gave out he sat on the verandah every afternoon watching the magpies. "
            "He could no longer dig or carry, but he loved to tell the grandchildren about Ballarat — "
            "the mud and the gold and Ah Fong who could balance a shilling on his thumbnail. "
            "He died in November 1918, the same week as the armistice. I think he was ready.",
        ),
    ],
    "thomas": [
        (
            "The grocery store on Collins Street",
            "I opened Kelly's Provisions in 1898 with two hundred pounds borrowed from my father. "
            "We sold flour, tea, tinned goods and tobacco. By 1910 we had three employees and a "
            "refrigerated cabinet — one of the first in Melbourne. The shop smelled of coffee "
            "and beeswax. I went there every morning at five-thirty for forty years.",
        ),
        (
            "Marrying Rose",
            "Rose Whitfield came to buy sugar and stayed to argue with me about the price of cream. "
            "She had strong opinions and a laugh that could stop traffic on Collins Street. "
            "We married in 1896 at St Patrick's Cathedral. My father wore his best suit and "
            "cried through the whole ceremony — embarrassing at the time, wonderful in memory.",
        ),
        (
            "The Great War years",
            "When war broke out in 1914 I was forty-four — too old to enlist, though I tried. "
            "Three of my shopmen went to Gallipoli. Only one came back. "
            "I kept their jobs open and paid their families a pound a week while they were away. "
            "It was the least I could do. The least.",
        ),
        (
            "Watching Melbourne grow",
            "In my lifetime Melbourne went from a tent city to a city of trams and electric lights. "
            "I remember the first motor car I ever saw — it frightened my horse and I nearly "
            "lost a case of Port Phillip butter into the gutter. The world moved faster every decade "
            "and I moved with it, even if my knees did not.",
        ),
        (
            "Teaching James the business",
            "James had his mother's quickness and my stubbornness. I wanted him to take over the shop, "
            "but he had his eye on the sky. When he joined the RAAF I was proud and terrified in equal measure. "
            "He came back, thank God. The shop passed to my nephew in the end — "
            "which was probably the right decision for everyone.",
        ),
    ],
    "rose": [
        (
            "Growing up in Adelaide",
            "My father was a schoolteacher from Somerset who settled in Adelaide in the 1860s. "
            "We had a garden full of roses — hence the name — and I learned to read before I learned "
            "to cook, which my mother considered the wrong order entirely. Adelaide was clean and quiet; "
            "Melbourne, when I arrived for Thomas, was noisy and magnificent.",
        ),
        (
            "Running the household",
            "Thomas managed the shop; I managed everything else. Five children, a house, a garden "
            "and a husband who thought meals appeared by magic. I kept account books for the household "
            "the same way Thomas kept them for the shop. Every penny recorded. Every debt paid on time. "
            "My children learned arithmetic helping me balance the household ledger.",
        ),
        (
            "The Spanish flu, 1919",
            "The influenza swept through Melbourne like a biblical plague. I set up a sick room "
            "in the parlour and nursed half the street. Thomas wore a gauze mask in the shop "
            "and we kept the children home from school for three months. "
            "We lost our neighbour Mrs Higgins. Her husband never quite recovered his spirit after that.",
        ),
        (
            "Joy of grandchildren",
            "When Robert was born in 1930 I held him in the kitchen while Thomas pretended not to cry "
            "in the hallway. Grandchildren are the reward for surviving parenthood. "
            "I taught Robert to bake soda bread the way my mother-in-law Brigid taught me. "
            "He still made it every year on St Patrick's Day, right up until he was in his seventies.",
        ),
    ],
    "james": [
        (
            "Enlisting in the RAAF",
            "I joined up in 1940. I was thirty-two — older than most of the boys in my flight. "
            "They called me 'Grandpa Kelly' until I outflew them all in the training circuit. "
            "I trained on Tiger Moths at Point Cook before converting to Kittyhawks. "
            "The Kittyhawk was a brute of a machine but it would get you home if you treated it right.",
        ),
        (
            "New Guinea, 1943",
            "We flew ground attack missions over the Owen Stanley Ranges — the most beautiful and "
            "terrible landscape I ever saw. Dense jungle, cloud that would kill you without warning, "
            "and Japanese AA fire that turned the air to iron. I lost my wingman Davies over Lae. "
            "I still hear the radio silence where his voice should have been.",
        ),
        (
            "Meeting Helen",
            "I met Helen Anderson at a dance at the Sydney Town Hall in June 1919. "
            "She was the best dancer in the room and she told me so herself. "
            "I asked her to dance three times and she said yes twice — which was already more "
            "than I deserved. We married the following spring at St Andrew's Cathedral. "
            "Her father William gave the toast in his best Scottish accent.",
        ),
        (
            "V-J Day in Sydney",
            "When the war in the Pacific ended I was in Brisbane. I drove to Sydney in a borrowed "
            "Ford and found Helen and the neighbours already dancing in the street. "
            "Robert was fifteen — old enough to understand what it meant. "
            "I held my son that night and promised myself I would never fly in anger again. I kept that promise.",
        ),
        (
            "Life after the war",
            "I worked for Qantas as a ground instructor after the war — close to the planes but "
            "not risking my neck. Helen and I moved to a brick house in Mosman. "
            "We had a garden, a dog named Digger, and Sunday roasts with whoever was passing through. "
            "Simple things. The best things.",
        ),
    ],
    "duncan": [
        (
            "Leaving Glasgow",
            "I sailed from the Clyde in 1862 at the age of twenty-four. My father had lost the croft "
            "to the landlord and there was nothing left in Scotland for a man without land. "
            "The voyage to Adelaide took ninety-three days. We rounded the Cape in a storm that "
            "knocked men from their bunks. I was afraid, but I did not go back.",
        ),
        (
            "The sheep station in the Flinders Ranges",
            "I selected six hundred acres in the Flinders Ranges in 1868. The country was hard "
            "and beautiful — red rock, saltbush, spinifex and a sky so big it made you feel "
            "both free and very small. I ran Merino sheep and sheared them myself "
            "in the early years before the station grew large enough for a crew.",
        ),
        (
            "The wool trade",
            "Good Merino fleece was worth real money in the 1870s. I shipped my clip to London "
            "via Port Augusta and kept careful records of every bale. In a good year we cleared "
            "two hundred pounds; in a drought year, nothing. "
            "The land taught me patience that nothing else could.",
        ),
        (
            "Building the homestead",
            "It took four years to build a stone homestead that would stand against the summer heat. "
            "The walls were two feet thick and the verandah ran all the way around. "
            "Flora planted a herb garden the day we moved in — rosemary, thyme and lavender "
            "that she had brought as cuttings from Scotland. They still grow there, I am told.",
        ),
        (
            "William leaving for Sydney",
            "When William told me he was going to Sydney I understood, even though it hurt. "
            "A young man needs to find his own country, just as I found mine. "
            "I shook his hand and told him to write every month. He wrote every two months. "
            "Good enough for a boy who had the whole harbour to look at.",
        ),
    ],
    "flora": [
        (
            "The voyage from Inverness",
            "I had never seen the ocean before I sailed from Glasgow in 1861 to join Duncan. "
            "The sea was nothing like the lochs at home — vast and indifferent and terrifying. "
            "I was sick for the first three weeks. By the fourth week I was cooking for the "
            "other passengers. By the twelfth week I had made three friends for life.",
        ),
        (
            "Managing the homestead",
            "While Duncan worked the sheep runs I kept the house, the kitchen garden and the accounts. "
            "We were forty miles from the nearest town. In emergencies I was doctor, "
            "farrier and postmistress all at once. I delivered two of our neighbour's children "
            "when the doctor could not reach us in time. Both survived.",
        ),
        (
            "The herb garden",
            "I brought cuttings from my mother's garden in Inverness — rosemary for remembrance, "
            "thyme for courage, lavender for calm. The South Australian sun was brutal but they survived. "
            "Every remedy I knew used herbs: feverfew for headaches, comfrey for bruises, "
            "peppermint for the stomach. The Aborigine women nearby taught me plants I had never seen before.",
        ),
        (
            "Teaching the children",
            "The nearest school was twenty miles away, so I taught our children myself. "
            "Reading, arithmetic, history and the Psalms. William was quick. Agnes was precise. "
            "I ran the lessons in the morning before the heat came. In the afternoon they worked "
            "beside us — that was the real education.",
        ),
    ],
    "william": [
        (
            "The harbour",
            "The first time I saw Sydney Harbour I stood on the ferry from Manly for twenty minutes "
            "unable to move. After twenty years in the outback the blue water and the sandstone cliffs "
            "were almost too much for the eyes. I knew immediately that I would stay. "
            "The harbour got under your skin and never left.",
        ),
        (
            "Working the wharves",
            "I started as a labourer on the Circular Quay wharves in 1888 and worked my way "
            "to foreman within five years. We unloaded wool bales, timber, coal and flour "
            "on twelve-hour shifts. The work was hard and the camaraderie was fierce. "
            "I loved those years on the water more than any other time in my working life.",
        ),
        (
            "Marrying Agnes",
            "Agnes was a nurse at Royal Prince Alfred Hospital when I met her at a church social in 1892. "
            "She had very straight posture and a completely direct way of looking at you "
            "that made lying seem futile. We were married within the year. "
            "She was right about everything important. I told her so, eventually.",
        ),
        (
            "Sydney Harbour Bridge construction",
            "I watched the bridge go up arch by arch from 1924 to 1932 from my window at Circular Quay. "
            "When they finally joined the two halves in August 1930, the crowd on the wharf cheered "
            "so loudly the pigeons didn't settle for an hour. "
            "I shook hands with every man on my crew. We felt we had built it ourselves.",
        ),
    ],
    "agnes": [
        (
            "Training as a nurse",
            "I trained at Royal Prince Alfred Hospital in 1890. In those days nursing was considered "
            "barely respectable for a woman of good family, which made it irresistible to me. "
            "The matron was a tyrant but a fair one. She taught me that medicine without compassion "
            "is merely mechanics, and compassion without skill is merely sentiment.",
        ),
        (
            "Managing the ward",
            "I was made ward sister in 1897 — one of the first women in New South Wales to hold "
            "the position. My ward was surgical. We had forty beds and two junior nurses. "
            "I ran it like my mother ran the homestead: everything accounted for, everything in its place, "
            "and no self-pity allowed on either side of the bedpan.",
        ),
        (
            "Raising Helen",
            "Helen grew up between the hospital and the harbour. She was as comfortable with sailors "
            "as with surgeons. I wanted her to train as a nurse but she had her father's eye for beauty "
            "and her own determination entirely. She found James at a dance and that was that. "
            "James was kind and brave. A mother can accept kindness and bravery.",
        ),
        (
            "The 1918 influenza",
            "The influenza of 1918 was the worst thing I saw in forty years of nursing. "
            "The wards filled in a week. We ran out of clean linen and sterilising solution "
            "and slept in two-hour shifts. Twenty-three of my patients died in a fortnight. "
            "I still say their names before I sleep. I always will.",
        ),
    ],
    "helen": [
        (
            "Sydney childhood",
            "I grew up between my father's wharves and my mother's hospital, which gave me "
            "a broad education in both rough weather and human frailty. "
            "The harbour was my playground. I could row a dinghy before I could ride a bicycle "
            "and I knew every ferry captain by name. Sydney was the most alive place on earth.",
        ),
        (
            "Meeting James at the Town Hall dance",
            "James Kelly asked me to dance at the Town Hall in June 1919. He was too old "
            "and too sure of himself and I told him both things. He laughed. I danced with him twice. "
            "By September I had decided to marry him, though I waited a decent interval before I told him so. "
            "He proposed in October, which was exactly when I intended.",
        ),
        (
            "The war years, waiting",
            "While James flew Kittyhawks over New Guinea I taught school in Mosman and wrote him "
            "a letter every week for five years. Some of them reached him; most did not. "
            "I kept copies of every letter in a biscuit tin under the bed. "
            "When James came home I read them to him on the verandah, one by one, through three evenings.",
        ),
        (
            "Robert's childhood",
            "Robert was born in 1930 in the middle of the Depression, which gave him both "
            "an appreciation for having enough and a horror of waste that lasted his whole life. "
            "He had James's eyes and my stubbornness, which was not always a comfortable combination. "
            "He was the cleverest person in every room he entered and the last to mention it.",
        ),
        (
            "Later life in Mosman",
            "James and I lived in Mosman for forty years. We had a garden, a dog and Sunday lunches "
            "that could last until sunset. After James died in 1968 I stayed in the house "
            "because every wall remembered him. I kept the garden going until I was eighty. "
            "The roses he planted by the front gate were still blooming when I left.",
        ),
    ],
    "robert": [
        (
            "A Depression childhood",
            "I was born in 1930 and grew up in the Depression years. We were not poor — "
            "my father's Qantas salary was steady — but the city around us was full of men "
            "without work. My mother made me collect the crusts from every meal and take them "
            "to the church soup kitchen on Friday afternoons. I have never thrown away bread since.",
        ),
        (
            "Watching the Opera House being built",
            "I had an office on Macquarie Street from 1958 and watched Jørn Utzon's shells "
            "rise year by year over Bennelong Point. It was an act of faith — nobody knew if "
            "the geometry would work until the first concrete ribs were in place. "
            "When it opened in October 1973 I was in the front row. I wept. My father would have loved it.",
        ),
        (
            "The Sydney property boom",
            "I spent my working life in property development — houses, flats, commercial buildings "
            "in the northern suburbs of Sydney. The city doubled in size between 1950 and 1980 "
            "and I built a small part of it. Brick veneer and fibro in the early years; "
            "good sandstone and recycled timber by the end. I changed my mind about what a building should be.",
        ),
        (
            "My grandfather Sean's stories",
            "My grandmother Brigid used to tell me about Sean's stories of the Ballarat goldfields. "
            "How Ah Fong taught him to pan in silence. How my great-grandmother wept into the Pacific "
            "on the way over and laughed when she saw the dirt floor of Footscray. "
            "That family came from nothing and built everything. It is the best inheritance they left me.",
        ),
        (
            "Family reunion, 1990",
            "In 1990 we gathered sixty-three members of the Kelly and Anderson families "
            "in a park in Mosman. My mother Helen was ninety-five and still the sharpest mind "
            "in the room. She stood up without notes and named every person there — "
            "their parents, their grandparents, how they connected. We were all thunderstruck. "
            "I hired a photographer and we have that day on the wall.",
        ),
    ],
}

# Event dates for life timeline (GET /memorials/{id}/timeline). Applied on insert and via patch for existing DBs.
EVENT_DATES = {
    ("sean", "Leaving Cork"): dt(1865, 1, 15),
    ("sean", "The Ballarat goldfields"): dt(1866, 6, 1),
    ("sean", "Building the house in Footscray"): dt(1872, 8, 1),
    ("sean", "Federation Day, 1901"): dt(1901, 1, 1),
    ("sean", "The drought years"): dt(1895, 4, 1),
    ("brigid", "The voyage from Cork"): dt(1871, 5, 20),
    ("brigid", "Raising five children in Ballarat"): dt(1875, 1, 1),
    ("brigid", "The Irish community in Melbourne"): dt(1890, 6, 15),
    ("brigid", "Sean's last years"): dt(1918, 11, 4),
    ("thomas", "The grocery store on Collins Street"): dt(1898, 3, 1),
    ("thomas", "Marrying Rose"): dt(1896, 4, 12),
    ("thomas", "The Great War years"): dt(1914, 8, 4),
    ("thomas", "Watching Melbourne grow"): dt(1920, 1, 1),
    ("thomas", "Teaching James the business"): dt(1935, 6, 1),
    ("rose", "Growing up in Adelaide"): dt(1865, 1, 1),
    ("rose", "Running the household"): dt(1897, 1, 1),
    ("rose", "The Spanish flu, 1919"): dt(1919, 3, 1),
    ("rose", "Joy of grandchildren"): dt(1930, 4, 11),
    ("james", "Enlisting in the RAAF"): dt(1940, 3, 1),
    ("james", "New Guinea, 1943"): dt(1943, 8, 1),
    ("james", "Meeting Helen"): dt(1919, 6, 14),
    ("james", "V-J Day in Sydney"): dt(1945, 8, 15),
    ("james", "Life after the war"): dt(1946, 1, 1),
    ("duncan", "Leaving Glasgow"): dt(1862, 3, 1),
    ("duncan", "The sheep station in the Flinders Ranges"): dt(1868, 6, 1),
    ("duncan", "The wool trade"): dt(1875, 1, 1),
    ("duncan", "Building the homestead"): dt(1872, 9, 1),
    ("duncan", "William leaving for Sydney"): dt(1888, 1, 1),
    ("flora", "The voyage from Inverness"): dt(1861, 8, 1),
    ("flora", "Managing the homestead"): dt(1875, 5, 1),
    ("flora", "The herb garden"): dt(1870, 4, 1),
    ("flora", "Teaching the children"): dt(1885, 3, 1),
    ("william", "The harbour"): dt(1885, 5, 1),
    ("william", "Working the wharves"): dt(1888, 3, 1),
    ("william", "Marrying Agnes"): dt(1892, 6, 1),
    ("william", "Sydney Harbour Bridge construction"): dt(1930, 8, 19),
    ("agnes", "Training as a nurse"): dt(1890, 2, 1),
    ("agnes", "Managing the ward"): dt(1897, 6, 1),
    ("agnes", "Raising Helen"): dt(1905, 1, 1),
    ("agnes", "The 1918 influenza"): dt(1918, 10, 1),
    ("helen", "Sydney childhood"): dt(1905, 1, 1),
    ("helen", "Meeting James at the Town Hall dance"): dt(1919, 6, 14),
    ("helen", "The war years, waiting"): dt(1942, 1, 1),
    ("helen", "Robert's childhood"): dt(1930, 4, 11),
    ("helen", "Later life in Mosman"): dt(1969, 1, 1),
    ("robert", "A Depression childhood"): dt(1935, 1, 1),
    ("robert", "Watching the Opera House being built"): dt(1973, 10, 20),
    ("robert", "The Sydney property boom"): dt(1965, 6, 1),
    ("robert", "My grandfather Sean's stories"): dt(1940, 7, 1),
    ("robert", "Family reunion, 1990"): dt(1990, 4, 1),
}


def apply_event_dates_to_existing(db):
    """Set event_date on seed memories so the timeline works after re-runs / old DBs."""
    updated = 0
    for key in MEMORIES:
        m_def = next((x for x in MEMORIALS if x["key"] == key), None)
        if not m_def:
            continue
        memorial = db.query(Memorial).filter(Memorial.name == m_def["name"]).first()
        if not memorial:
            continue
        for title, content in MEMORIES[key]:
            ed = EVENT_DATES.get((key, title))
            if not ed:
                continue
            mem = db.query(Memory).filter(
                Memory.memorial_id == memorial.id,
                Memory.title == title,
            ).first()
            if mem and getattr(mem, "source", None) == "seed":
                mem.event_date = ed
                updated += 1
    if updated:
        db.commit()
        print(f"\n📅 Timeline: set event_date on {updated} seed memories (existing rows).")


# ── Family relationships ──────────────────────────────────────────────────────
# Format: (from_key, to_key, type)
RELATIONSHIPS = [
    # Gen 1 Kelly – spouses
    ("sean", "brigid", RelationshipType.SPOUSE),
    ("brigid", "sean", RelationshipType.SPOUSE),
    # Sean & Brigid → Thomas
    ("sean", "thomas", RelationshipType.PARENT),
    ("brigid", "thomas", RelationshipType.PARENT),
    ("thomas", "sean", RelationshipType.CHILD),
    ("thomas", "brigid", RelationshipType.CHILD),
    # Gen 2 Kelly – spouses
    ("thomas", "rose", RelationshipType.SPOUSE),
    ("rose", "thomas", RelationshipType.SPOUSE),
    # Thomas & Rose → James
    ("thomas", "james", RelationshipType.PARENT),
    ("rose", "james", RelationshipType.PARENT),
    ("james", "thomas", RelationshipType.CHILD),
    ("james", "rose", RelationshipType.CHILD),
    # Gen 1 Anderson – spouses
    ("duncan", "flora", RelationshipType.SPOUSE),
    ("flora", "duncan", RelationshipType.SPOUSE),
    # Duncan & Flora → William
    ("duncan", "william", RelationshipType.PARENT),
    ("flora", "william", RelationshipType.PARENT),
    ("william", "duncan", RelationshipType.CHILD),
    ("william", "flora", RelationshipType.CHILD),
    # Gen 2 Anderson – spouses
    ("william", "agnes", RelationshipType.SPOUSE),
    ("agnes", "william", RelationshipType.SPOUSE),
    # William & Agnes → Helen
    ("william", "helen", RelationshipType.PARENT),
    ("agnes", "helen", RelationshipType.PARENT),
    ("helen", "william", RelationshipType.CHILD),
    ("helen", "agnes", RelationshipType.CHILD),
    # Cross-family: James ∞ Helen
    ("james", "helen", RelationshipType.SPOUSE),
    ("helen", "james", RelationshipType.SPOUSE),
    # James & Helen → Robert
    ("james", "robert", RelationshipType.PARENT),
    ("helen", "robert", RelationshipType.PARENT),
    ("robert", "james", RelationshipType.CHILD),
    ("robert", "helen", RelationshipType.CHILD),
]


async def seed():
    db = SessionLocal()
    try:
        # Ensure owner user exists
        owner = db.query(User).filter(User.id == 1).first()
        if not owner:
            print("⚠️  No user with id=1 found. Please create a user first (run the app once).")
            return

        created: dict[str, Memorial] = {}

        for m_def in MEMORIALS:
            key = m_def["key"]
            # Idempotent: skip if memorial with this name already exists
            existing = db.query(Memorial).filter(Memorial.name == m_def["name"]).first()
            if existing:
                print(f"⏭️  Skipping {m_def['name']} (already exists, id={existing.id})")
                created[key] = existing
                continue

            memorial = Memorial(
                name=m_def["name"],
                description=m_def.get("desc"),
                birth_date=m_def.get("birth"),
                death_date=m_def.get("death"),
                is_public=True,
                voice_gender=m_def.get("voice_gender"),
                language="en",
                owner_id=1,
            )
            db.add(memorial)
            db.flush()

            # Grant owner access
            access = MemorialAccess(
                memorial_id=memorial.id,
                user_id=1,
                role=UserRole.OWNER,
            )
            db.add(access)
            db.commit()
            db.refresh(memorial)
            created[key] = memorial
            print(f"✅ Created memorial: {memorial.name} (id={memorial.id})")

        # Add memories + embeddings
        for key, memory_list in MEMORIES.items():
            memorial = created.get(key)
            if not memorial:
                continue
            for title, content in memory_list:
                ev = EVENT_DATES.get((key, title))
                existing_mem = db.query(Memory).filter(
                    Memory.memorial_id == memorial.id,
                    Memory.title == title,
                ).first()
                if existing_mem:
                    print(f"  ⏭️  Memory '{title}' already exists for {memorial.name}")
                    continue

                memory = Memory(
                    memorial_id=memorial.id,
                    title=title,
                    content=content,
                    source="seed",
                    event_date=ev,
                )
                db.add(memory)
                db.flush()

                try:
                    text = f"{title}: {content}"
                    embedding = await get_embedding(text)
                    embedding_id = await upsert_memory_embedding(
                        memory_id=memory.id,
                        memorial_id=memorial.id,
                        text=text,
                        embedding=embedding,
                        title=title,
                    )
                    memory.embedding_id = embedding_id
                    db.commit()
                    print(f"  📝 Memory + embedding: '{title}' (memorial={memorial.id})")
                except Exception as e:
                    db.rollback()
                    print(f"  ❌ Embedding failed for '{title}': {e}")
                    # Save memory without embedding
                    memory = Memory(
                        memorial_id=memorial.id,
                        title=title,
                        content=content,
                        source="seed",
                        event_date=ev,
                    )
                    db.add(memory)
                    db.commit()
                    print(f"  📝 Memory saved without embedding: '{title}'")

        apply_event_dates_to_existing(db)

        # Add family relationships (idempotent)
        for from_key, to_key, rel_type in RELATIONSHIPS:
            from_m = created.get(from_key)
            to_m = created.get(to_key)
            if not from_m or not to_m:
                continue
            existing_rel = db.query(FamilyRelationship).filter(
                FamilyRelationship.memorial_id == from_m.id,
                FamilyRelationship.related_memorial_id == to_m.id,
                FamilyRelationship.relationship_type == rel_type,
            ).first()
            if not existing_rel:
                rel = FamilyRelationship(
                    memorial_id=from_m.id,
                    related_memorial_id=to_m.id,
                    relationship_type=rel_type,
                )
                db.add(rel)

        db.commit()
        print("\n✅ Family relationships created.")
        print(f"\n🏁 Seed complete. Memorials created: {len([k for k in created if created[k]])}")
        print("   Switch to EN in the UI to see the Australian families.")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(seed())
