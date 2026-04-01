"""
Seed: part 3 of 3 — two EN family clusters (Chang + Rossi). После цепочки `seed_english_all.py` в БД **35** EN мемориалов.

Список имён: `en_memorials_manifest.py`. После сида добавляются рёбра `custom` в `family_relationships`,
чтобы full-tree с любого демо-мемориала включал Kelly, Anderson, Chang и Rossi (одна компонента связности).

CLUSTER 3 — Chang family (Chinese-Australian, Ballarat goldfields):
  Ah Fong Chang (1835-1895)  ← already mentioned in Sean Kelly's memories
  Wei Chang (1868-1942) + Mei Lin Wu Chang (1872-1950)
  Thomas Chang (1898-1968) + Alice Lee Chang (1902-1978)
  Richard Chang (1930-2010) + Grace Kim Chang (1934–alive)
  David Chang (1962–alive) + Jennifer Park Chang (1964–alive)

CLUSTER 4 — Rossi family (Italian-Australian, Sicily → Sydney 1952):
  Enzo Rossi (1920-1988) + Maria Conti Rossi (1925-2008)
  Antonio Rossi (1950-alive) + Giulia Moretti Rossi (1952-alive)
  Marco Rossi (1978-alive) + Sofia Ferrara Rossi (1980-alive)

HIDDEN CONNECTIONS created:
  Chang ↔ Kelly:    Ah Fong Chang + Sean Kelly shared a Ballarat claim (1866-1868)
  Rossi ↔ Kelly:    Enzo Rossi built houses Robert Kelly developed (northern Sydney, 1960s)
                    Antonio Rossi was subcontractor on Michael Kelly's Rocks restoration (1990s)
  Rossi ↔ Anderson: Antonio Rossi and Ian Anderson worked adjacent Sydney Harbour Tunnel (1990)
  Chang ↔ Anderson: Wei Chang's market garden, Neutral Bay — same street as Anderson flat

Run from backend/:
    source .venv/bin/activate && python seed_english_cluster2.py
"""

import asyncio, sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from datetime import datetime, timezone
from app.db import SessionLocal, engine
from app.models import (Base, Memorial, Memory, FamilyRelationship,
                        RelationshipType, MemorialAccess, User, UserRole)
from app.services.ai_tasks import get_embedding, upsert_memory_embedding

Base.metadata.create_all(bind=engine)

def dt(year, month=1, day=1):
    return datetime(year, month, day, tzinfo=timezone.utc)


# ── CLUSTER 3: Chang family ───────────────────────────────────────────────────
CHANG_MEMORIALS = [
    {
        "key": "ahfong",
        "name": "Ah Fong Chang",
        "birth": dt(1835, 4, 5),
        "death": dt(1895, 8, 12),
        "voice_gender": "male",
        "desc": "Chinese gold miner from Guangdong Province. Arrived in Victoria in 1856. Worked the Ballarat and Bendigo fields for twenty years before settling in Melbourne as a market gardener.",
    },
    {
        "key": "wei",
        "name": "Wei Chang",
        "birth": dt(1868, 2, 14),
        "death": dt(1942, 5, 30),
        "voice_gender": "male",
        "desc": "Son of Ah Fong Chang. Born in Ballarat, grew up in the Melbourne Chinese community. Established a market garden in Neutral Bay, Sydney, supplying hotels and restaurants for forty years.",
    },
    {
        "key": "meilin",
        "name": "Mei Lin Wu Chang",
        "birth": dt(1872, 9, 3),
        "death": dt(1950, 1, 18),
        "voice_gender": "female",
        "desc": "Born in Guangdong, arrived in Melbourne at fifteen to marry Wei Chang. Managed the household accounts and the garden stall at the North Sydney markets for three decades.",
    },
    {
        "key": "thomas_chang",
        "name": "Thomas Chang",
        "birth": dt(1898, 11, 22),
        "death": dt(1968, 3, 7),
        "voice_gender": "male",
        "desc": "Son of Wei and Mei Lin Chang. Opened the first Chang family restaurant on Military Road, Neutral Bay, in 1928. Served as local councillor 1950-58.",
    },
    {
        "key": "alice",
        "name": "Alice Lee Chang",
        "birth": dt(1902, 6, 18),
        "death": dt(1978, 11, 4),
        "voice_gender": "female",
        "desc": "Born in Sydney's Chinatown to a family from Fujian Province. Married Thomas Chang in 1926. Ran the restaurant kitchen for forty years and taught Cantonese cooking to three generations.",
    },
    {
        "key": "richard_chang",
        "name": "Richard Chang",
        "birth": dt(1930, 8, 9),
        "death": dt(2010, 2, 14),
        "voice_gender": "male",
        "desc": "Son of Thomas and Alice Chang. Studied law at Sydney University. Became one of the first Chinese-Australian barristers in NSW. Retired to Manly after forty years at the bar.",
    },
    {
        "key": "grace",
        "name": "Grace Kim Chang",
        "birth": dt(1934, 3, 25),
        "death": None,  # alive
        "voice_gender": "female",
        "desc": "Korean-Australian. Married Richard Chang in 1958. Former high school principal in Manly. Still active in the local multicultural community at ninety-one.",
    },
    {
        "key": "david_chang",
        "name": "David Chang",
        "birth": dt(1962, 7, 11),
        "death": None,  # alive
        "voice_gender": "male",
        "desc": "Son of Richard and Grace Chang. Architect and urban planner. Worked on the Sydney 2000 Olympic precinct and the Barangaroo development. Lives in Balmain.",
    },
    {
        "key": "jennifer",
        "name": "Jennifer Park Chang",
        "birth": dt(1964, 5, 30),
        "death": None,  # alive
        "voice_gender": "female",
        "desc": "Korean-Australian restaurateur. Married David Chang in 1990. Runs three contemporary Asian restaurants in Sydney. Founded the Sydney Asian Culinary Foundation in 2005.",
    },
]

CHANG_MEMORIES = {
    "ahfong": [
        (
            "Leaving Guangdong",
            "I left Guangdong Province in 1856 at twenty-one years old. "
            "The elders called Australia 'Gam Saan' — Gold Mountain. "
            "The ship took three months. When we arrived at Port Phillip "
            "the immigration officers could not pronounce my name and wrote 'Ah Fong' "
            "in their ledger. That became my name in Australia. "
            "I kept my true name for myself, for prayers, for my ancestors.",
        ),
        (
            "The Ballarat fields",
            "By 1858 the easy gold at Ballarat was gone. "
            "The Chinese miners worked together in groups — sharing water, sharing tools, "
            "taking the tailings the Europeans had abandoned. "
            "We found colour where others found nothing because we were patient "
            "and because we did not waste what we found. "
            "My claim in 1866 was on a creek two lots over from an Irishman named Kelly. "
            "He was a quiet man and a careful miner. We nodded each morning.",
        ),
        (
            "Sean Kelly — the Irishman at Eureka",
            "The Irish miner Sean Kelly and I worked adjacent claims on Specimen Creek "
            "from 1866 to 1868. He had strong hands and patience — rare qualities in a goldfield. "
            "He asked me once how to pan without disturbing the heavy minerals. "
            "I showed him: tilt slowly, let the water decide, watch the bottom. "
            "He was a good student. In those years the goldfields were full of noise and anger; "
            "Sean Kelly was neither. I respected that.",
        ),
        (
            "The Lambing Flat riots",
            "The violence against Chinese miners in the 1860s was real and constant. "
            "At Lambing Flat they drove three thousand Chinese from the fields "
            "with clubs and fire. We heard the news at Ballarat and held meetings at night "
            "to decide whether to leave. Most of us stayed. "
            "We had come twelve thousand miles. We would not be driven twelve miles.",
        ),
        (
            "Moving to Melbourne",
            "After the gold I moved to Melbourne and grew vegetables on a small plot "
            "in Fitzroy. I sent money home to Guangdong every year. "
            "I married in 1867 — a woman from a Fujian family who had come out with her brother. "
            "We had three children. Wei was the eldest. "
            "I told him: this country is difficult and yours. Both things are true.",
        ),
        (
            "The vegetable garden",
            "The soil in Melbourne was good after Ballarat rock. "
            "I grew bok choy, Chinese cabbage, water spinach — things the markets had never seen. "
            "The restaurant owners came to me because I grew what no one else could. "
            "In twenty years the garden fed my family, sent my children to school, "
            "and built a house. The gold never did that. The soil did.",
        ),
        (
            "Teaching Wei the garden",
            "When Wei was old enough I gave him the accounts and the market contacts. "
            "He had his mother's precision and my patience. "
            "He moved to Sydney in 1892 because the restaurant trade was bigger there. "
            "He found land in Neutral Bay and grew the business to twice what I had built. "
            "I was glad. That is what a parent hopes: that the next generation builds further.",
        ),
        (
            "What I kept from the goldfields",
            "From Ballarat I kept three things: the habit of silence, "
            "the knowledge that gold is where no one else has looked, "
            "and the memory of Sean Kelly's face on a cold morning, "
            "crouching over the creek, learning to listen to the water. "
            "I wonder sometimes what became of him. "
            "The goldfields scattered men like seeds. Most of them grew somewhere.",
        ),
        (
            "A letter I never sent",
            "I wrote a letter to my father in Guangdong in 1870 telling him "
            "what Australia was. I described the heat and the dust and the violence "
            "and the strange beauty of the bush at dawn when the birds began. "
            "I described the creek at Ballarat and the colour of gold in water. "
            "I described Sean Kelly who taught himself to pan by watching me. "
            "I never sent the letter. The distance was too large for a letter to cross. "
            "I kept it. Wei has it now.",
        ),
        (
            "Old age in Fitzroy",
            "In my last years I sat in the garden in Fitzroy and watched the tomatoes grow. "
            "Sixty years from Guangdong to this quiet plot. "
            "I had found no great fortune. I had built something that lasted. "
            "Wei was in Sydney with his market garden. His children would go further still. "
            "That is how it works: each generation takes what the last one built "
            "and carries it one step further. "
            "I carried it from Guangdong to Ballarat to Fitzroy. Wei will carry it to Neutral Bay.",
        ),
    ],

    "wei": [
        (
            "Growing up in Melbourne",
            "I was born in Ballarat in 1868 and grew up in my father's Fitzroy garden. "
            "The vegetables were my school: every variety had a name, a season, a use. "
            "My father Ah Fong grew things no one else in Melbourne knew to grow, "
            "and sold them to restaurants who paid well for the unfamiliar. "
            "I learned from him that knowing something no one else knows "
            "is worth more than knowing what everyone knows.",
        ),
        (
            "Neutral Bay market garden",
            "I moved to Sydney in 1892 and found land at Neutral Bay — "
            "good deep soil, close to the harbour, near the restaurants of Military Road. "
            "The Anderson family had a flat two streets away. "
            "Their boy William worked the Circular Quay wharves and sometimes bought "
            "vegetables from my stall at the North Sydney market. "
            "He had his father's directness. A good customer and a decent man.",
        ),
        (
            "The North Sydney market",
            "At the North Sydney market every Saturday I set up before dawn. "
            "The harbour was visible from the corner of the stall — "
            "grey-green water going gold as the sun came up. "
            "My father had mined gold in the ground. "
            "I watched it every morning in the harbour and was content with that.",
        ),
        (
            "Father's letter about Sean Kelly",
            "My father Ah Fong left me a letter he had never sent to his own father. "
            "In it he described the Ballarat goldfields and a man named Sean Kelly — "
            "an Irish miner on the adjacent claim who learned to pan gold in silence. "
            "I kept that letter. Many years later I showed it to Thomas, my son. "
            "He said: the world is smaller than we think. I said: yes. "
            "And the small parts connect in ways we don't expect.",
        ),
        (
            "Mei Lin and the accounts",
            "Mei Lin came from Guangdong at fifteen to marry me — "
            "an arrangement made between our families before she arrived. "
            "In the first year she learned English faster than I had in twenty. "
            "By the second year she was keeping the garden accounts "
            "in a notation I had never seen and could not challenge. "
            "By the third year the accounts were more accurate than they had ever been. "
            "She ran the market stall. I grew the vegetables. We did well.",
        ),
        (
            "Thomas and the restaurant",
            "When Thomas said he was going to open a restaurant I thought: "
            "my father grew what no one else could; I sold it to restaurants. "
            "Thomas will cook it and sell it directly. Three generations, one chain. "
            "He opened on Military Road in 1928. By 1935 it was the best-known "
            "restaurant in Neutral Bay. I was proud without words. "
            "Ah Fong would have been very proud. He would not have said that either.",
        ),
        (
            "The Depression years",
            "The Depression hit the market garden hard. "
            "Restaurant orders dropped by half. I extended credit to Thomas's restaurant "
            "and to two others I knew would survive. "
            "Mei Lin sold at the market herself every Saturday for three years, "
            "which she had not done since the early days. "
            "We came through. When the orders came back I did not raise prices. "
            "The restaurateurs remembered that for twenty years.",
        ),
        (
            "The harbour from Neutral Bay",
            "My father described the harbour in his unsent letter as something "
            "he had not expected — blue and enormous and full of ships. "
            "I watched it from Neutral Bay for fifty years. "
            "It never became ordinary. Every morning was different light. "
            "When William Anderson's boy George walked past the garden on his way "
            "to school I sometimes waved. He waved back. "
            "The harbour connected everyone who lived near it.",
        ),
    ],

    "meilin": [
        (
            "The voyage from Guangdong",
            "I arrived in Sydney at fifteen, having agreed to marry a man "
            "I had never met, in a country I had never seen. "
            "My mother told me: Wei Chang is a good man from a good family. "
            "He will work hard and you will build something. "
            "She was right on all three counts. "
            "The voyage took two months. I was sick for the first three weeks "
            "and cooked for the other passengers from the fourth week onward. "
            "It seemed the right response.",
        ),
        (
            "Learning English",
            "I learned English from the women at the North Sydney market — "
            "Italian women, Irish women, a Scottish woman named Mrs Fraser "
            "who sold cheese and was very particular about grammar. "
            "I learned the names of vegetables in English, then prices, "
            "then weather, then politics. "
            "By the third year I was translating for the other Chinese stallholders. "
            "Language is not difficult if you listen more than you speak.",
        ),
        (
            "The market stall and the Andersons",
            "Agnes Anderson — the nurse from the hospital — bought vegetables "
            "from our stall every Saturday for twenty years. "
            "She was exact about quality and fair about price and never wasted a word. "
            "I liked her. We did not socialise — the world did not work that way then — "
            "but we understood each other. "
            "Two women running things while their husbands did the visible work. "
            "We knew what that meant.",
        ),
        (
            "Teaching Alice the kitchen",
            "When Thomas married Alice Lee in 1926 I taught her everything "
            "my mother taught me: the balance of flavour, the order of the wok, "
            "how to taste before you season. "
            "Alice was quick and had her own ideas, which I encouraged. "
            "A kitchen that never changes is a kitchen that is not living. "
            "She made the restaurant what it was. "
            "I made her the cook she was. That is enough.",
        ),
        (
            "Neutral Bay in the 1930s",
            "By the 1930s Neutral Bay was changing — more Italians, more Europeans, "
            "the Depression making everyone careful. "
            "The vegetable garden kept selling because people still ate. "
            "Thomas's restaurant was full on Friday and Saturday. "
            "The world was difficult outside our street. "
            "Inside our street we managed. "
            "Wei said: the vegetables don't know about the Depression. "
            "He was right. That helped.",
        ),
        (
            "Richard growing up",
            "Richard was the serious one — always reading, always asking questions "
            "that didn't have easy answers. At ten he asked why Chinese miners "
            "in Ballarat had been attacked and no one went to prison for it. "
            "I told him the truth: because the law did not protect us then. "
            "He said: I will change that. "
            "He studied law at Sydney University in 1949 "
            "and was called to the bar in 1954. "
            "He changed it.",
        ),
        (
            "Wei's last years",
            "Wei died in 1942 while I still had years left. "
            "I ran the garden accounts alone for three more years before Richard "
            "took them over. "
            "Wei had been right about everything important: "
            "the land, the market, the children, the patience. "
            "He had his father Ah Fong's habit of saying the necessary thing once "
            "and not repeating it. "
            "I still hear his voice in the garden in the mornings. "
            "I hope I always will.",
        ),
    ],

    "thomas_chang": [
        (
            "Military Road restaurant, 1928",
            "I opened Chang's on Military Road in 1928 with three hundred pounds "
            "borrowed from my parents and a wok that had been my grandmother's in Guangdong. "
            "The first night we served twelve customers. "
            "By the third month we were full every Friday and Saturday. "
            "Neutral Bay in 1928 had never had a Chinese restaurant. "
            "By 1930 it could not imagine being without one.",
        ),
        (
            "Alice and the kitchen",
            "Alice Lee ran the kitchen from the day we married. "
            "She had learned to cook in her mother's house in Chinatown "
            "and then refined it through twenty years of her own invention. "
            "My job was the front of house — the customers, the suppliers, the council. "
            "Her job was everything that made people come back. "
            "That is not a small job. It is the whole job.",
        ),
        (
            "The Depression and the restaurant",
            "In the Depression years we fed people who could not always pay. "
            "I kept a book of what was owed. At the end of 1933 I burned the book. "
            "What was owed was owed to us by people who had nothing. "
            "My father Wei had done the same with vegetable credit in the 1930s. "
            "Some things you learn from watching, not from being taught.",
        ),
        (
            "My grandfather Ah Fong's letter",
            "My father Wei gave me Ah Fong's unsent letter when I was twenty. "
            "In it my grandfather described a man named Sean Kelly "
            "on an adjacent claim at Ballarat — an Irish miner who learned to pan "
            "by watching Ah Fong in silence. "
            "I have thought about that letter many times. "
            "Two men from opposite ends of the world, crouching over the same creek, "
            "teaching each other patience without a shared language. "
            "That is a more Australian story than most people tell.",
        ),
        (
            "Becoming a councillor",
            "I was elected to the North Sydney Council in 1950. "
            "The first Chinese-Australian councillor in the area. "
            "The campaign was not easy — there were people who voted against me "
            "because of what I was rather than what I would do. "
            "There were more who voted for me because of what I would do. "
            "I served eight years. I am prouder of the eight years than of the election.",
        ),
        (
            "Richard and the law",
            "Richard wanted to be a barrister from the age of twelve "
            "and was one by thirty. "
            "He argued cases that my grandfather Ah Fong would never have believed "
            "could be won: discrimination cases, land cases, cases where the law "
            "was used as a weapon against people like us. "
            "He won more than he lost. "
            "The law changed slowly. Richard pushed it consistently. "
            "That is the right speed for pushing the law.",
        ),
        (
            "The restaurant after forty years",
            "By 1968 Chang's on Military Road had been open for forty years. "
            "Alice and I had served three generations of Neutral Bay families. "
            "Some of the grandchildren of our first customers brought their own grandchildren. "
            "When I died in March 1968 Alice kept the restaurant open. "
            "She said: closing would be the wrong kind of memorial. "
            "She was right. She usually was.",
        ),
    ],

    "alice": [
        (
            "Growing up in Chinatown",
            "I grew up in Dixon Street, Sydney — the Chinatown of the 1910s, "
            "which smelled of dried fish and fireworks and the particular kind of noise "
            "that comes from many families living close together with strong opinions. "
            "My father was from Fujian, my mother from Guangdong. "
            "I grew up speaking three dialects and one kind of English "
            "and chose my husband from the better-organized of the Sydney Chinese families.",
        ),
        (
            "Marrying Thomas",
            "Thomas Chang was serious and ambitious and had a plan — "
            "a restaurant on Military Road, a house in Neutral Bay, "
            "a life that was visible to the neighbourhood. "
            "I said yes because he had a plan and because he was honest about it. "
            "Plans can be discussed and adjusted. "
            "Men without plans cannot be discussed at all.",
        ),
        (
            "The kitchen at Military Road",
            "The kitchen at Chang's was my laboratory for forty years. "
            "I changed the menu every season and kept the classics every night. "
            "I trained six head cooks over the years, all of whom went on "
            "to their own restaurants. "
            "I told each of them: a kitchen is a conversation. "
            "You are always answering a question the customer hasn't asked yet.",
        ),
        (
            "Mei Lin's teaching",
            "My mother-in-law Mei Lin Wu Chang was the best cook I ever knew "
            "and the most precise person in any room. "
            "She taught me the wok technique that came from her mother in Guangdong "
            "and from her own forty years of market cooking. "
            "I changed what she taught me. She encouraged that. "
            "She said: a recipe that doesn't change is a recipe that isn't alive.",
        ),
        (
            "The regular customers",
            "The Andersons from Neutral Bay were Friday regulars for twenty years. "
            "George Anderson — the mathematics teacher — brought his wife Margaret "
            "every Friday until he died in 1965. "
            "Margaret continued coming alone for years after. "
            "I knew their order before they sat down. "
            "That is what regulars are: people who trust you with their Friday evening.",
        ),
        (
            "Keeping the restaurant after Thomas",
            "When Thomas died in 1968 I kept Chang's open. "
            "Richard offered to sell it. I said no. "
            "Thomas had built it. I had built it with him. "
            "The closing would have been a statement I was not prepared to make. "
            "I ran it for another ten years until Richard's children were old enough "
            "to decide if they wanted it. "
            "David chose architecture instead. I told him: good. "
            "A building lasts longer than a restaurant.",
        ),
        (
            "Richard at the bar",
            "Richard was called to the bar in 1954 and argued his first case "
            "against a landlord who had refused to rent to a Chinese family. "
            "He won. The landlord appealed. Richard won the appeal. "
            "The landlord complained to the Bar Association. "
            "The Bar Association found for Richard. "
            "I kept the judgment on the restaurant wall until I retired. "
            "Thomas would have done the same.",
        ),
    ],

    "richard_chang": [
        (
            "Sydney University and the law",
            "I read law at Sydney University from 1949 to 1953. "
            "In those years there were very few Chinese-Australian students "
            "at the faculty. The law was not hostile — it was indifferent, "
            "which is a different and more persistent problem. "
            "Indifference can be changed by presence. I was present. "
            "I argued every tutorial. I published in the law review in third year. "
            "Indifference eventually has to respond to evidence.",
        ),
        (
            "The first discrimination case",
            "My first significant case was a landlord who refused to rent "
            "to a Chinese family in Mosman in 1955. "
            "The law at that time barely covered the situation. "
            "I argued on common law principles and won. "
            "The decision was narrow but it was a decision. "
            "Every subsequent discrimination case in NSW that decade cited it. "
            "A narrow win in the right direction is worth more than a wide win "
            "that points nowhere.",
        ),
        (
            "Ah Fong's letter",
            "My father Thomas gave me Ah Fong's unsent letter when I was thirty. "
            "By then I had been a barrister for four years and had argued "
            "cases about the rights my grandfather never had. "
            "Reading the letter I felt the weight of what he had survived: "
            "the riots, the exclusion, the indifference of the law. "
            "And beside it, his description of Sean Kelly at Ballarat — "
            "the Irish miner who learned patience from watching a Chinese man. "
            "Two outsiders, helping each other. That is also a legal principle, "
            "if you look at it from the right angle.",
        ),
        (
            "Grace and the school",
            "Grace Kim was a teacher at the school I taught at on Saturdays "
            "for the Chinese community. She taught English to newly arrived families "
            "with a precision and warmth I had not seen combined before. "
            "I asked her to dinner three times before she said yes. "
            "The third time she said: I was waiting to see if you were persistent. "
            "I said: I am a barrister. Persistence is the qualification.",
        ),
        (
            "Manly and retirement",
            "Grace and I moved to Manly after I retired from the bar in 1992. "
            "We had lived in Neutral Bay — where the garden had been, "
            "where the restaurant had been — for thirty years. "
            "Manly was different light, different water. "
            "In Manly I met Ian Anderson at the beach — an old civil engineer, "
            "also retired, also walking every morning. "
            "We talked about the Harbour Tunnel, which he had helped build. "
            "We talked about the law, which I had helped change. "
            "Two old men from completely different families, "
            "with more connections than either of us had known.",
        ),
        (
            "Ian Anderson at Manly beach",
            "Ian Anderson told me one morning at Manly beach that his grandfather "
            "William Anderson had bought vegetables from a Chinese market gardener "
            "in Neutral Bay in the 1890s. "
            "I said: that was my grandfather Wei Chang. "
            "Ian looked at me for a long time. "
            "Then he said: Grace — your wife — teaches at the same school "
            "where my wife Evelyn runs the Highland dance evenings. "
            "We had been connected for three generations "
            "without knowing it once. "
            "I told him about Ah Fong and Sean Kelly. "
            "He said: the world is a very small creek at Ballarat.",
        ),
        (
            "David and architecture",
            "David chose architecture over the law, which I thought was a loss "
            "and have since decided was a gain. "
            "He designed the interpretation centre at the old Ballarat goldfields in 2001 — "
            "a building that tells the story of Chinese and Irish and Scottish and Italian miners "
            "who worked the same creek beds in the 1860s. "
            "He found a Ballarat census record from 1867 that listed "
            "'Ah Fong Chang, miner, China' two claims from 'Sean Kelly, miner, Ireland.' "
            "He put them both in the building. "
            "I wept when I saw it. Not loud. But I wept.",
        ),
    ],

    "grace": [
        (
            "Coming to Australia from Seoul",
            "I arrived in Sydney in 1953 from Seoul at nineteen — "
            "my parents had sent me to live with my aunt after the Korean War. "
            "Sydney was warm and incomprehensible. "
            "I learned English at night school and was teaching it within two years. "
            "Language is the first door. Once you have it everything else is practice.",
        ),
        (
            "Teaching and the community",
            "I taught English to newly arrived Chinese, Korean, Italian and Greek families "
            "on Saturday mornings at the Neutral Bay community centre for fifteen years. "
            "Every family was different. Every difficulty was the same: "
            "how do you become a person in a language you don't yet own? "
            "The answer is: slowly, with help, and with the patience of people "
            "who remember their own slowly.",
        ),
        (
            "Richard and the first dinner",
            "Richard Chang asked me to dinner three times before I said yes. "
            "The first time I said: I'm busy. "
            "The second time I said: another time. "
            "The third time I said: yes, but choose somewhere interesting. "
            "He chose his mother's restaurant on Military Road. "
            "Alice Chang cooked for us specifically. "
            "That was the correct answer. I married him the following year.",
        ),
        (
            "Alice Chang's kitchen",
            "Alice Chang was the most confident person in any kitchen I entered. "
            "She moved with a certainty that made the wok seem like an extension of herself. "
            "She taught me three dishes that I still make: "
            "her version of her mother Mei Lin's, which was Mei Lin's version of her mother's. "
            "Three generations from Guangdong to Neutral Bay in one recipe.",
        ),
        (
            "Evelyn Anderson at the Highland dance",
            "I met Evelyn Parker Anderson at the Manly Scottish Association "
            "where she ran the Highland dance evenings. "
            "I am not Scottish and had never attempted Highland dance. "
            "Evelyn told me: it's applied geometry. Come and learn. "
            "I came and learned. We have been friends for thirty years. "
            "She dances with precision and I follow with application. "
            "It works.",
        ),
        (
            "Manly and the connections",
            "In Manly we discovered that our families had been connected "
            "for three generations without knowing it. "
            "Richard and Ian Anderson talked at the beach about "
            "their grandfathers — Wei Chang and William Anderson — "
            "who had both been at North Sydney market in the 1890s. "
            "Richard found Ah Fong's letter. Ian found the Neutral Bay rate records. "
            "David built a database. It turned out we had been neighbours "
            "for a hundred years without being introduced.",
        ),
        (
            "The Ballarat interpretation centre",
            "When David designed the Ballarat interpretation centre "
            "he asked me and Evelyn to contribute community perspectives. "
            "I wrote about the Chinese miners — Ah Fong's generation — "
            "what they brought, what they survived, what they built. "
            "Evelyn wrote about the Scottish settlers. "
            "We worked side by side at my kitchen table. "
            "Two women from different continents, writing about different men, "
            "who had stood two claims apart on the same creek in 1866. "
            "The world is made of these distances and these proximities.",
        ),
    ],

    "david_chang": [
        (
            "Architecture and heritage",
            "I studied architecture at Sydney University in the early 1980s "
            "and specialised in heritage interpretation — buildings that tell stories. "
            "My grandfather Thomas's restaurant had told a story for forty years "
            "simply by existing. My great-grandfather's garden in Neutral Bay "
            "had told a story by growing things no one else in Sydney grew. "
            "I wanted to design buildings that told stories on purpose, "
            "for people who had never heard them.",
        ),
        (
            "The Barangaroo project",
            "The Barangaroo development in the early 2000s was the largest urban project "
            "I worked on. We were designing public spaces where the old wharves had been — "
            "the same wharves where William Anderson had worked as foreman in the 1890s, "
            "though I didn't know that then. "
            "Michael Kelly's heritage firm had done preliminary documentation on the site. "
            "We used his reports. I met him once at a site briefing. "
            "We talked about what remains when the physical structure is gone. "
            "He said: memory. I agreed.",
        ),
        (
            "The Ballarat interpretation centre",
            "The Ballarat Goldfields Interpretation Centre was the project "
            "that changed my understanding of what architecture is for. "
            "I found Ah Fong's census record in the Ballarat archive — "
            "claim number, location, adjacent miners. "
            "Two claims over: Sean Kelly, miner, Ireland. "
            "I put them both in the building. Not as heroes. As people. "
            "Two men who came from opposite ends of the world "
            "and crouched over the same creek in silence in 1866. "
            "I wept when the building opened. My father Richard wept beside me.",
        ),
        (
            "Daniel Kelly and the archive",
            "Daniel Kelly — a software engineer whose family history overlaps with mine "
            "in ways neither of us fully maps — built a database of "
            "the Kelly and Anderson families that includes references to Ah Fong Chang. "
            "He found the Ballarat census on his own, looking for Sean Kelly's neighbours. "
            "He contacted me through the interpretation centre website. "
            "We met for coffee in Balmain and talked for three hours. "
            "The world is a creek in Ballarat and we are all two claims over from each other.",
        ),
        (
            "Jennifer and the restaurants",
            "Jennifer Park arrived in Sydney in 1988 from Seoul — "
            "the same city my mother Grace had come from thirty-five years earlier. "
            "She walked into my office to discuss the fit-out of her first restaurant "
            "and we talked for four hours about food, memory, and what a room should feel like. "
            "We married in 1990. She has built three restaurants. "
            "I have built their rooms. It is the best collaboration I have found.",
        ),
        (
            "The family archive",
            "My father Richard kept Ah Fong's unsent letter. "
            "My grandmother Alice kept the restaurant on Military Road after Thomas died. "
            "My great-grandmother Mei Lin kept the accounts in her notation "
            "that nobody else could read. "
            "My great-great-grandfather Ah Fong kept the habit of silence "
            "that he taught to a man named Sean Kelly. "
            "I keep the buildings. "
            "I make the rooms where other people's stories are told. "
            "That is what the family has always done: "
            "held what matters until the next person can carry it.",
        ),
    ],

    "jennifer": [
        (
            "Seoul to Sydney, 1988",
            "I arrived in Sydney from Seoul in 1988 at twenty-four "
            "with a hospitality degree and a certainty that I would open a restaurant. "
            "Sydney in 1988 was loud and fast and full of opportunity "
            "and completely unprepared for what I intended to cook. "
            "That was, I quickly realised, an advantage.",
        ),
        (
            "Meeting David",
            "David Chang walked into my first restaurant opening — "
            "he had designed the room — and spent four hours "
            "arguing with me about whether the lighting was right for the food. "
            "He was correct that it wasn't. "
            "I told him to fix it and invited him to dinner. "
            "We married two years later. "
            "The lighting in our house has been excellent ever since.",
        ),
        (
            "The Sydney Asian Culinary Foundation",
            "I founded the Sydney Asian Culinary Foundation in 2005 "
            "to preserve and document the food history of Asian communities in NSW. "
            "The first oral history project was with elderly Chinese-Australian women "
            "who had been cooking in Sydney for sixty years — "
            "women like Alice Lee Chang, Thomas's wife, who had learned from Mei Lin "
            "who had learned from her mother in Guangdong. "
            "These recipes are not in books. They are in the hands of women "
            "who are running out of time to pass them on.",
        ),
        (
            "Grace Kim Chang's kitchen",
            "My mother-in-law Grace kept a kitchen that was part Korean, part Chinese, "
            "part Australian, and entirely her own. "
            "She told me: a kitchen reflects where you have been "
            "and where you are now, but it only works if it reflects you. "
            "That is the most useful cooking advice I have received. "
            "I apply it in all three restaurants.",
        ),
        (
            "Evelyn Anderson and the Foundation",
            "Evelyn Parker Anderson — Grace's friend from the Highland dance evenings — "
            "joined the Foundation's advisory board in 2010. "
            "She connected us to the Scottish-Australian food history that overlapped "
            "with the Chinese and Irish histories in Ballarat and Sydney. "
            "Flora Anderson had brought cuttings from Inverness. "
            "Ah Fong Chang had brought seeds from Guangdong. "
            "They both planted them in Australian soil in the 1860s. "
            "Different plants. Same impulse.",
        ),
    ],
}

CHANG_RELATIONSHIPS = [
    ("ahfong", "wei", RelationshipType.PARENT),
    ("wei", "ahfong", RelationshipType.CHILD),
    ("wei", "meilin", RelationshipType.SPOUSE),
    ("meilin", "wei", RelationshipType.SPOUSE),
    ("wei", "thomas_chang", RelationshipType.PARENT),
    ("meilin", "thomas_chang", RelationshipType.PARENT),
    ("thomas_chang", "wei", RelationshipType.CHILD),
    ("thomas_chang", "meilin", RelationshipType.CHILD),
    ("thomas_chang", "alice", RelationshipType.SPOUSE),
    ("alice", "thomas_chang", RelationshipType.SPOUSE),
    ("thomas_chang", "richard_chang", RelationshipType.PARENT),
    ("alice", "richard_chang", RelationshipType.PARENT),
    ("richard_chang", "thomas_chang", RelationshipType.CHILD),
    ("richard_chang", "alice", RelationshipType.CHILD),
    ("richard_chang", "grace", RelationshipType.SPOUSE),
    ("grace", "richard_chang", RelationshipType.SPOUSE),
    ("richard_chang", "david_chang", RelationshipType.PARENT),
    ("grace", "david_chang", RelationshipType.PARENT),
    ("david_chang", "richard_chang", RelationshipType.CHILD),
    ("david_chang", "grace", RelationshipType.CHILD),
    ("david_chang", "jennifer", RelationshipType.SPOUSE),
    ("jennifer", "david_chang", RelationshipType.SPOUSE),
]


# ── CLUSTER 4: Rossi family ───────────────────────────────────────────────────
ROSSI_MEMORIALS = [
    {
        "key": "enzo",
        "name": "Enzo Rossi",
        "birth": dt(1920, 5, 3),
        "death": dt(1988, 9, 14),
        "voice_gender": "male",
        "desc": "Sicilian immigrant who arrived in Sydney in 1952. Construction worker who built houses across the northern suburbs. His brickwork is in buildings that are still standing in Mosman, Cremorne and Neutral Bay.",
    },
    {
        "key": "maria",
        "name": "Maria Conti Rossi",
        "birth": dt(1925, 12, 8),
        "death": dt(2008, 4, 22),
        "voice_gender": "female",
        "desc": "Born in Palermo, Sicily. Arrived in Sydney with Enzo in 1952. Ran the family vegetable garden in Cremorne and was a pillar of the Italian community at St Canice's Church, Elizabeth Bay.",
    },
    {
        "key": "antonio",
        "name": "Antonio Rossi",
        "birth": dt(1950, 8, 19),
        "death": None,  # alive
        "voice_gender": "male",
        "desc": "Son of Enzo and Maria Rossi. Builder and heritage stonemason. Worked as lead stonemason on Michael Kelly's Rocks restoration project 1992-98. Still runs Rossi Heritage Stoneworks from his yard in Leichhardt.",
    },
    {
        "key": "giulia",
        "name": "Giulia Moretti Rossi",
        "birth": dt(1952, 3, 15),
        "death": None,  # alive
        "voice_gender": "female",
        "desc": "Born in Calabria, Italy. Arrived in Sydney at twelve. Married Antonio Rossi in 1975. Works as a community interpreter and has been a volunteer at the Leichhardt Neighbourhood Centre for thirty years.",
    },
    {
        "key": "marco",
        "name": "Marco Rossi",
        "birth": dt(1978, 11, 7),
        "death": None,  # alive
        "voice_gender": "male",
        "desc": "Son of Antonio and Giulia Rossi. Structural engineer. Worked on the Sydney Barangaroo development where his path crossed David Chang's. Lives in Balmain with his family.",
    },
    {
        "key": "sofia",
        "name": "Sofia Ferrara Rossi",
        "birth": dt(1980, 6, 24),
        "death": None,  # alive
        "voice_gender": "female",
        "desc": "Italian-Australian documentary filmmaker. Married Marco Rossi in 2006. Her 2015 documentary 'The Wharves' interviewed Ian Anderson about his memories of the Harbour Tunnel construction.",
    },
]

ROSSI_MEMORIES = {
    "enzo": [
        (
            "Leaving Sicily, 1952",
            "I left Palermo in March 1952 on a boat with four hundred other Sicilians "
            "going to Australia under the assisted passage scheme. "
            "The government paid ten pounds for the ticket. "
            "The conditions were that we work for two years wherever they sent us. "
            "They sent me to Sydney. I have never once wished they had sent me anywhere else.",
        ),
        (
            "Learning to build in Sydney",
            "My first job was labouring on a housing estate in Baulkham Hills — "
            "brick veneer houses going up in straight lines across paddocks. "
            "In Sicily I had worked stone. Brick was different: faster, more uniform, "
            "less beautiful, more practical. "
            "I learned it in six months and was a bricklayer in a year. "
            "By 1955 I had my own small crew.",
        ),
        (
            "Building in Mosman",
            "Robert Kelly was the developer who gave me my biggest contracts "
            "in the early 1960s. He was building houses in the northern suburbs — "
            "Mosman, Cremorne, Neutral Bay — and he wanted good brickwork. "
            "I gave him good brickwork. He paid fairly and on time, "
            "which in the construction industry is the highest compliment. "
            "We worked together for fifteen years. "
            "His houses are still standing. So is my brickwork.",
        ),
        (
            "Robert Kelly the developer",
            "Robert Kelly told me once: a house is an argument about what lasts. "
            "He had changed his mind about building as he got older — "
            "away from cheap and fast, toward solid and permanent. "
            "I agreed with him. In Sicily the old buildings were still standing "
            "because someone had built them to last. "
            "I tried to build that way in every house. "
            "Robert Kelly understood why.",
        ),
        (
            "Maria and the Cremorne garden",
            "Maria made a vegetable garden behind our Cremorne house "
            "that fed the family and half the street. "
            "Tomatoes, eggplant, zucchini, beans — the Sicilian garden "
            "in Australian soil. "
            "The Chinese family two streets over — Wei Chang's grandchildren — "
            "grew vegetables for the restaurants. "
            "Maria used to trade seeds with them. Different vegetables, same instinct.",
        ),
        (
            "Antonio learning the trade",
            "Antonio learned bricklaying from me and then went beyond it. "
            "He found old stonework — convict-era sandstone, colonial bluestone — "
            "and taught himself how to read it and repair it. "
            "When the heritage restoration work started in the 1980s "
            "Antonio was better prepared than anyone in Sydney. "
            "I did not plan that. He followed the stone where it led.",
        ),
        (
            "St Canice's and the Italian community",
            "Maria kept us connected to the Italian community through St Canice's. "
            "Sunday mass, the festa of our village saint in August, "
            "the women's cooking group on Tuesday evenings. "
            "The Church was Italy in Sydney — smaller and louder and full of argument "
            "about things that had been settled for decades. "
            "I loved it. It reminded me that I was from somewhere, "
            "even when Sydney tried to make me from nowhere.",
        ),
        (
            "What I built",
            "In thirty years I laid brick in more than two hundred buildings "
            "across the northern suburbs of Sydney. "
            "I built with Robert Kelly for fifteen years. "
            "I built churches, schools, houses, a library. "
            "I did not design them. I made them stand. "
            "That is a different skill, and not a lesser one.",
        ),
    ],

    "maria": [
        (
            "Palermo before I left",
            "Palermo in 1952 was poor and beautiful and full of people "
            "who had been poor and beautiful for a very long time. "
            "My family had survived the war by growing food and hiding it. "
            "When the government offered ten-pound passages to Australia "
            "my father said: go. You will have a better life. "
            "He was right. I have never not been grateful to him.",
        ),
        (
            "The voyage out",
            "The boat to Sydney took thirty-two days. "
            "Four hundred Sicilians in close quarters with strong opinions "
            "about food and politics and each other. "
            "I made friends with three women who became my closest friends "
            "for the next forty years. "
            "One of them is buried ten metres from me at the Rookwood Cemetery. "
            "The others are still in Leichhardt. We talk every week.",
        ),
        (
            "The Cremorne garden",
            "The soil in Cremorne was good — deep and red and responsive. "
            "I planted Sicilian seeds I had brought in a cloth bag: "
            "the long eggplant, the San Marzano tomato, the bitter chicory. "
            "The Australian sun was more than they were used to "
            "but they adapted. Sicilian vegetables are stubborn. "
            "They survive because they have had to.",
        ),
        (
            "Trading seeds with the Chang family",
            "Wei Chang's grandchildren — the Chang family from Neutral Bay — "
            "had moved to Cremorne by the time we arrived. "
            "Their garden was extraordinary: things I had never seen, "
            "varieties from Guangdong Province that needed no translation "
            "to understand as food. "
            "We traded seeds and cuttings and recipes across the back fence for twenty years. "
            "Mei Lin Chang's seeds are still growing in my garden.",
        ),
        (
            "St Canice's and the women's group",
            "The Tuesday cooking group at St Canice's was the best cooking school "
            "I attended in Australia. Sicilian, Calabrian, Neapolitan, Venetian — "
            "every region argued that theirs was the correct method. "
            "After three years I understood that every region was right "
            "about its own dishes and wrong about everyone else's. "
            "This is also true of families.",
        ),
        (
            "Enzo and the Kelly contract",
            "Robert Kelly gave Enzo the biggest contracts of his career "
            "in the early 1960s. "
            "I met Patricia Kelly once — Robert's wife — at a site visit. "
            "She was a schoolteacher who had come to look at the kitchen layout. "
            "She stood in the empty room and told the foreman exactly what was wrong "
            "with the window placement. "
            "The foreman changed it. The window was right. "
            "A woman who knows what she wants and can describe it clearly — "
            "I respected that completely.",
        ),
        (
            "Antonio and the stonework",
            "When Antonio found the old sandstone buildings and started to repair them "
            "I understood something I had not quite seen before: "
            "that the old building was the message and the restoration was the translation. "
            "My son spoke two languages fluently: the language of new buildings "
            "and the language of old ones. "
            "Enzo taught him the first. The stone taught him the second.",
        ),
        (
            "Giulia joining the family",
            "Giulia Moretti came from Calabria at twelve and grew up in Leichhardt. "
            "When Antonio brought her home I looked at her hands — "
            "a woman's hands tell you what she has been doing. "
            "Her hands had worked. I approved. "
            "She has been working ever since. "
            "Marco is her best work. I tell her that regularly.",
        ),
    ],

    "antonio": [
        (
            "Learning stone from Enzo",
            "My father Enzo laid brick with a precision that I was not conscious of "
            "until I tried to match it and couldn't. "
            "Brick has a logic: coursing, bonding, the joint between. "
            "Stone has a different logic: every piece is different and the joint "
            "must find itself. Enzo showed me brick. Stone I had to find on my own. "
            "I found it in the old buildings of The Rocks and Paddington "
            "that were being cleared for development in the 1970s.",
        ),
        (
            "The Rocks restoration — Michael Kelly",
            "Michael Kelly's firm contacted me in 1992 to lead the stonework "
            "on a heritage restoration in The Rocks. "
            "I had worked with his father Robert's developments in the 1970s — "
            "I knew the Kelly name in construction before I met Michael. "
            "Michael was different from Robert: he thought about stone "
            "the way I did — as a language rather than a material. "
            "We worked together for six years. The Rocks restoration "
            "is the best work I have done in this city.",
        ),
        (
            "What Michael Kelly understood",
            "Michael Kelly said once: restoration is not reconstruction. "
            "You are not making it new. You are making it legible. "
            "The building has been through things. Your job is to let it say what it knows. "
            "I have used that sentence in every project since. "
            "It is the most accurate description of stonework I have heard "
            "from someone who does not lay stone.",
        ),
        (
            "The Harbour Tunnel years",
            "While I was working on heritage restoration in the 1990s "
            "the Sydney Harbour Tunnel was being built two kilometres away. "
            "Ian Anderson — the civil engineer — was on that project. "
            "We met at a builders' association dinner in 1990. "
            "I told him I was restoring nineteenth-century sandstone above the water. "
            "He told me he was boring a tunnel under it. "
            "We agreed: the harbour is a very busy workplace. "
            "We had dinner several times after that. His wife Evelyn and Giulia became friends.",
        ),
        (
            "Ian Anderson and the engineering",
            "Ian Anderson understood what I did with old stone "
            "the way an engineer understands structure: "
            "as a problem that has already been solved once "
            "and needs to be understood rather than replaced. "
            "He told me about his grandfather William Anderson "
            "who had worked the Circular Quay wharves — "
            "the same wharves I was restoring warehouse records for. "
            "The city folds back on itself, he said. "
            "I said: and the stone remembers everything.",
        ),
        (
            "Marco and structural engineering",
            "Marco chose structural engineering over stonemason work, "
            "which I understood even while I hoped he would stay with the stone. "
            "He sees load paths and stress distributions where I see joints and bedding planes. "
            "Different language, same instinct: "
            "how does this thing stay up? "
            "We argue about methods at Sunday lunch. "
            "His wife Sofia records the arguments for her documentaries. "
            "I am not sure I have won one yet.",
        ),
        (
            "Robert Kelly's houses",
            "In the 1970s I worked on Robert Kelly's developments in the northern suburbs. "
            "His houses were solid — he had moved away from fibro and veneer "
            "toward good brick and recycled sandstone. "
            "My father Enzo had worked with Robert in the 1960s on the brick veneer estates. "
            "I worked with Robert in the 1970s on the better buildings. "
            "Robert never mentioned that Enzo had worked for him before. "
            "He had probably forgotten. I hadn't.",
        ),
        (
            "Rossi Heritage Stoneworks",
            "I have run Rossi Heritage Stoneworks from the Leichhardt yard since 1985. "
            "We restore colonial-era stone across NSW — courthouses, churches, wharves, walls. "
            "Every building has a logic that the original builders put there "
            "and that needs to be read before it can be repaired. "
            "I have been reading buildings for forty years. "
            "I have never finished learning the language.",
        ),
    ],

    "giulia": [
        (
            "Calabria to Leichhardt",
            "My family came from Calabria to Leichhardt in 1964 when I was twelve. "
            "Leichhardt in 1964 was Italy at a distance: "
            "the same noise and smell and argument, "
            "but with a harbour outside the window instead of the Ionian Sea. "
            "I learned English at school and Italian again at home. "
            "The two versions of me have never quite agreed on everything.",
        ),
        (
            "Community interpreting",
            "I have worked as a community interpreter for thirty years — "
            "Italian, Spanish, a little Portuguese. "
            "At hospitals, at courts, at immigration interviews. "
            "The work is not translating words. It is translating situations. "
            "A word in Italian carries a context in Italian. "
            "The English equivalent carries a different context. "
            "My job is to find the meaning between them.",
        ),
        (
            "Marrying Antonio",
            "Antonio Rossi came to our house with his father Enzo "
            "to look at a wall that needed repointing. "
            "He looked at the wall for ten minutes before he touched it. "
            "I found that interesting. "
            "A man who looks before he acts is a man who thinks before he acts. "
            "That is not common enough. "
            "We married in 1975.",
        ),
        (
            "Evelyn Anderson and the women's group",
            "Evelyn Anderson — Ian Anderson's wife — and I met at the Leichhardt "
            "Neighbourhood Centre where she was running a community information session "
            "and I was interpreting for an Italian family. "
            "After the session we had coffee and talked for two hours. "
            "She told me about the Sydney Scottish community and the Highland dances. "
            "I told her about the Italian community and the Tuesday cooking group. "
            "Different dances. Same reason for dancing.",
        ),
        (
            "Antonio and Michael Kelly",
            "When Antonio worked with Michael Kelly on The Rocks restoration "
            "I watched the collaboration from a distance and thought: "
            "these are two people who speak the same language "
            "and have never been introduced to each other before. "
            "Michael talked about buildings as conversations. "
            "Antonio talked about stone as language. "
            "They were saying the same thing in different materials. "
            "Catherine Kelly — Michael's wife — was writing it all down.",
        ),
        (
            "Marco and Sofia",
            "Marco is more like Enzo than like Antonio — he builds big things fast. "
            "Sofia is more like me — she asks questions and waits for the full answer. "
            "Together they slow each other down to the right speed. "
            "That is what a good marriage does: "
            "each person provides what the other lacks "
            "without making the other feel the lack.",
        ),
        (
            "The Leichhardt centre",
            "Thirty years at the Leichhardt Neighbourhood Centre. "
            "Thousands of families who came through not knowing what Australia was "
            "and left knowing a little more. "
            "I think of my twelve-year-old self arriving from Calabria "
            "with no English and a mother who spoke only dialect. "
            "I was that family. "
            "I have spent thirty years being what someone was for us then. "
            "That is the only accounting that makes sense to me.",
        ),
    ],

    "marco": [
        (
            "Growing up in Leichhardt",
            "Leichhardt in the 1980s was the centre of Italian Sydney — "
            "coffee, argument, football on Saturday afternoon, "
            "and my father Antonio talking about stone over dinner "
            "in a way that made structural engineering seem romantic. "
            "I chose engineering because of him and despite him. "
            "He wanted me in the stone. I wanted to understand "
            "why the stone stayed where it was. Different questions, same building.",
        ),
        (
            "The Barangaroo project",
            "Barangaroo was the biggest project I worked on — "
            "the redevelopment of the old container wharves into public space and towers. "
            "David Chang was the heritage architect on the site interpretation. "
            "We worked in adjacent buildings for eight months. "
            "He told me that his great-great-grandfather's market garden had been "
            "two kilometres from this site. "
            "My grandfather Enzo had laid brick in the Mosman houses "
            "of the developer Robert Kelly, whose son Michael had documented "
            "this very site before David arrived. "
            "Sydney is a very small city with very long memory.",
        ),
        (
            "David Chang and the family histories",
            "David Chang introduced me to Daniel Kelly "
            "— the software engineer who had built the Kelly-Anderson family archive — "
            "at a Barangaroo site dinner in 2020. "
            "Daniel showed me the archive on his phone. "
            "He had found Enzo Rossi in the council building permits from 1962 — "
            "listed as the bricklayer on a Robert Kelly development in Mosman. "
            "I had not known that. "
            "I rang my father Antonio that evening to tell him. "
            "He already knew. He had just never mentioned it.",
        ),
        (
            "Antonio and The Rocks",
            "My father Antonio told me about working with Michael Kelly "
            "on the Rocks restoration from 1992 to 1998. "
            "He described Michael the same way he describes stone: "
            "something that has a logic you have to find rather than impose. "
            "Antonio said Michael was the best client he ever had "
            "because Michael asked questions instead of issuing instructions. "
            "I try to work that way. It is harder than it sounds.",
        ),
        (
            "Ian Anderson's Harbour Tunnel",
            "Ian Anderson had engineered the Sydney Harbour Tunnel "
            "while Antonio was restoring the stone above the harbour. "
            "When Sofia filmed 'The Wharves' she interviewed Ian in Manly. "
            "He told her: the tunnel is under what the wharves were over. "
            "Every generation finds a different way to cross the same water. "
            "Sofia used that as the last line of the film. "
            "It is accurate and it is beautiful and Ian said it without thinking about it.",
        ),
        (
            "The archive connection",
            "Daniel Kelly's archive is the most useful thing "
            "I have found for understanding what this city actually is — "
            "not the postcard version but the working version: "
            "who built what for whom, who lived near whom, "
            "who worked on the same harbour a generation apart. "
            "My grandfather Enzo is in there: bricklayer, Mosman, 1962. "
            "Ah Fong Chang is in there: miner, Ballarat, 1867. "
            "Sean Kelly is in there, two claims over from Ah Fong. "
            "All of us, building the same city from different directions.",
        ),
    ],

    "sofia": [
        (
            "Documentary filmmaking",
            "I came to documentary filmmaking through journalism — "
            "I was covering community stories for SBS in the late 2000s "
            "and realised that the people I was interviewing had more to say "
            "than a three-minute segment could hold. "
            "A documentary is a longer conversation. "
            "I am interested in the conversations that have not been finished yet.",
        ),
        (
            "The Wharves — interviewing Ian Anderson",
            "For 'The Wharves' I interviewed Ian Anderson at Manly beach "
            "where he walks every morning at ninety-three. "
            "He told me about his grandfather William who had worked Circular Quay "
            "for forty years, and about his own work on the Harbour Tunnel. "
            "He said: the tunnel is under what the wharves were over. "
            "Every generation finds a different way to cross the same water. "
            "I used that as the last line of the film. "
            "Ian cried when he saw the finished documentary. "
            "He said: I didn't know I had said something that good.",
        ),
        (
            "Marrying Marco",
            "Marco Rossi designs how things stand up. "
            "I document how things fall down. "
            "We argued about this at dinner for a year before we married "
            "and have continued arguing about it for fifteen years since. "
            "The argument has not resolved because we are both right. "
            "Structure and change: both necessary, both real.",
        ),
        (
            "Antonio and the stone",
            "My father-in-law Antonio walks into old buildings "
            "and starts reading them the way I read faces — "
            "for what has happened, what has lasted, what has changed. "
            "He ran his hand along a sandstone wall in The Rocks once "
            "and told me the name of the quarry, the decade the stone was cut, "
            "and why the joint on the left corner had been repaired by a different hand. "
            "I filmed it. That ten seconds is in three different documentaries now.",
        ),
        (
            "Jennifer Chang's restaurant archive",
            "Jennifer Park Chang's Asian Culinary Foundation has the most complete "
            "archive of food history I have found in Sydney. "
            "She connected me to elderly Chinese-Australian women "
            "whose families had been in Sydney since the 1860s. "
            "I filmed twelve oral histories for the Foundation. "
            "One of the women remembered Wei Chang's market garden in Neutral Bay — "
            "she had bought vegetables there as a child. "
            "Her memory was clearer than any written record.",
        ),
        (
            "The Ballarat film",
            "After 'The Wharves' I made a film about the Ballarat goldfields "
            "using David Chang's interpretation centre as the visual anchor. "
            "The centre tells the story of Ah Fong Chang and Sean Kelly "
            "on adjacent claims in 1866. "
            "I filmed at the creek where the claim was registered. "
            "The water still runs there. The gold is long gone. "
            "The story is not.",
        ),
        (
            "The connected families",
            "After three years of filming across these families — "
            "Kelly, Anderson, Chang, Rossi — I have come to understand "
            "that Sydney is not a city of separate communities. "
            "It is a city of overlapping ones that have been told they are separate. "
            "Enzo Rossi built Robert Kelly's houses. "
            "Antonio Rossi restored Michael Kelly's Rocks buildings. "
            "Wei Chang sold vegetables to Agnes Anderson. "
            "Grace Chang dances with Evelyn Anderson. "
            "Ah Fong Chang taught Sean Kelly patience at a creek in Ballarat. "
            "None of them knew all of this at once. "
            "Now, through Daniel Kelly's archive and David Chang's building "
            "and my films, they can.",
        ),
    ],
}

# Мосты между кластерами (исторические связи из сюжета демо). Двунаправленные CUSTOM.
CROSS_CLUSTER_CUSTOM_BRIDGES = [
    ("Sean Patrick Kelly", "Ah Fong Chang"),
    ("Wei Chang", "Agnes Brown Anderson"),
    ("Robert James Kelly", "Enzo Rossi"),
    ("Michael Robert Kelly", "Antonio Rossi"),
    ("Antonio Rossi", "Ian George Anderson"),
]


def _ensure_custom_bridge_pair(db, name_a: str, name_b: str) -> None:
    ma = db.query(Memorial).filter(Memorial.name == name_a).first()
    mb = db.query(Memorial).filter(Memorial.name == name_b).first()
    if not ma or not mb:
        print(f"  ⚠️  Bridge skipped (memorial not found): {name_a!r} ↔ {name_b!r}")
        return
    rt = RelationshipType.CUSTOM
    for src, dst in ((ma.id, mb.id), (mb.id, ma.id)):
        exists = (
            db.query(FamilyRelationship)
            .filter(
                FamilyRelationship.memorial_id == src,
                FamilyRelationship.related_memorial_id == dst,
                FamilyRelationship.relationship_type == rt,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            FamilyRelationship(
                memorial_id=src,
                related_memorial_id=dst,
                relationship_type=rt,
            )
        )
        print(f"  🌉 CUSTOM bridge {src} → {dst}")
    db.commit()


ROSSI_RELATIONSHIPS = [
    ("enzo", "maria", RelationshipType.SPOUSE),
    ("maria", "enzo", RelationshipType.SPOUSE),
    ("enzo", "antonio", RelationshipType.PARENT),
    ("maria", "antonio", RelationshipType.PARENT),
    ("antonio", "enzo", RelationshipType.CHILD),
    ("antonio", "maria", RelationshipType.CHILD),
    ("antonio", "giulia", RelationshipType.SPOUSE),
    ("giulia", "antonio", RelationshipType.SPOUSE),
    ("antonio", "marco", RelationshipType.PARENT),
    ("giulia", "marco", RelationshipType.PARENT),
    ("marco", "antonio", RelationshipType.CHILD),
    ("marco", "giulia", RelationshipType.CHILD),
    ("marco", "sofia", RelationshipType.SPOUSE),
    ("sofia", "marco", RelationshipType.SPOUSE),
]


async def seed():
    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.id == 1).first()
        if not owner:
            print("⚠️  No user with id=1.")
            return

        created: dict[str, Memorial] = {}

        all_memorials = CHANG_MEMORIALS + ROSSI_MEMORIALS
        all_memories = {**CHANG_MEMORIES, **ROSSI_MEMORIES}
        all_relationships = CHANG_RELATIONSHIPS + ROSSI_RELATIONSHIPS

        # ── Create memorials ──────────────────────────────────────────────
        for m_def in all_memorials:
            key = m_def["key"]
            existing = db.query(Memorial).filter(Memorial.name == m_def["name"]).first()
            if existing:
                print(f"⏭️  Skipping {m_def['name']} (id={existing.id})")
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
            db.add(MemorialAccess(memorial_id=memorial.id, user_id=1, role=UserRole.OWNER))
            db.commit()
            db.refresh(memorial)
            created[key] = memorial
            print(f"✅ Created: {memorial.name} (id={memorial.id})")

        # ── Add memories ──────────────────────────────────────────────────
        for key, memory_list in all_memories.items():
            memorial = created.get(key)
            if not memorial:
                print(f"  ⚠️  Not found: {key}")
                continue
            await _add_memories(db, memorial, memory_list)

        # ── Add relationships ─────────────────────────────────────────────
        from sqlalchemy import text as sql_text
        for fk, tk, rt in all_relationships:
            fid = created.get(fk)
            tid = created.get(tk)
            if not fid or not tid:
                print(f"  ⚠️  Skipping {fk}→{tk}")
                continue
            fid = fid.id if hasattr(fid, 'id') else fid
            tid = tid.id if hasattr(tid, 'id') else tid
            exists = engine.connect().execute(sql_text(
                "SELECT id FROM family_relationships WHERE memorial_id=:a AND related_memorial_id=:b AND relationship_type=:rt LIMIT 1"
            ), {"a": fid, "b": tid, "rt": rt.value}).fetchone()
            if not exists:
                with engine.connect() as c:
                    c.execute(sql_text(
                        "INSERT INTO family_relationships (memorial_id, related_memorial_id, relationship_type) VALUES (:a,:b,:rt)"
                    ), {"a": fid, "b": tid, "rt": rt.value})
                    c.commit()
                print(f"  🔗 {fk}({fid}) --{rt.value}--> {tk}({tid})")

        print("\n── Cross-cluster CUSTOM bridges (Kelly/Anderson ↔ Chang/Rossi) ──")
        for na, nb in CROSS_CLUSTER_CUSTOM_BRIDGES:
            _ensure_custom_bridge_pair(db, na, nb)

        with engine.connect() as c:
            total_en = c.execute(sql_text("SELECT COUNT(*) FROM memorials WHERE language='en'")).fetchone()[0]
            total_rel = c.execute(sql_text("SELECT COUNT(*) FROM family_relationships")).fetchone()[0]

        print(f"\n✅ Done. EN memorials: {total_en} | Total relationships: {total_rel}")

    finally:
        db.close()


async def _add_memories(db, memorial: Memorial, memory_list: list):
    for title, content in memory_list:
        existing = db.query(Memory).filter(
            Memory.memorial_id == memorial.id,
            Memory.title == title,
        ).first()
        if existing:
            continue
        memory = Memory(memorial_id=memorial.id, title=title, content=content, source="seed")
        db.add(memory)
        db.flush()
        try:
            text = f"{title}: {content}"
            embedding = await get_embedding(text)
            eid = await upsert_memory_embedding(
                memory_id=memory.id, memorial_id=memorial.id,
                text=text, embedding=embedding, title=title,
            )
            memory.embedding_id = eid
            db.commit()
            print(f"  📝 {memorial.name}: '{title}'")
        except Exception as e:
            db.rollback()
            memory = Memory(memorial_id=memorial.id, title=title, content=content, source="seed")
            db.add(memory)
            db.commit()
            print(f"  📝 {memorial.name}: '{title}' (no embedding: {e})")


if __name__ == "__main__":
    asyncio.run(seed())
