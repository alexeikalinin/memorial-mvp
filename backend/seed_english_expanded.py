"""
Expanded EN seed: part 2 of 3 — adds 9 new memorials + extended memories for all 11 existing.

Итого по цепочке: **35** EN после `seed_english_all.py` (11+9+15). Список имён: `en_memorials_manifest.py`.

New memorials:
  Kelly Gen 4: Robert + Patricia Ann Murphy Kelly (1935-2010)
  Kelly Gen 5: Michael Robert Kelly (1958-2019) + Catherine O'Neill Kelly (b.1960, alive)
  Kelly Gen 6: Sarah Elizabeth Kelly (b.1985, alive), Daniel James Kelly (b.1988, alive)
  Anderson Gen 3 (William+Agnes's son): George William Anderson (1900-1965) + Margaret Fraser Anderson (1904-1985)
  Anderson Gen 4: Ian George Anderson (b.1932, alive) + Evelyn Parker Anderson (b.1935, alive)

Total after this run: 20 EN memorials (was 11).

Run from backend/:
    source .venv/bin/activate && python seed_english_expanded.py
"""

import asyncio, sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from datetime import datetime, timezone
from app.db import SessionLocal, engine
from app.models import Base, Memorial, Memory, FamilyRelationship, RelationshipType, MemorialAccess, User, UserRole
from app.services.ai_tasks import get_embedding, upsert_memory_embedding

Base.metadata.create_all(bind=engine)


def dt(year, month=1, day=1):
    return datetime(year, month, day, tzinfo=timezone.utc)


# ── NEW memorials ─────────────────────────────────────────────────────────────
NEW_MEMORIALS = [
    # Kelly Gen 4 – Robert's wife
    {
        "key": "patricia",
        "name": "Patricia Ann Murphy Kelly",
        "birth": dt(1935, 8, 22),
        "death": dt(2010, 3, 5),
        "voice_gender": "female",
        "desc": "Irish-Australian schoolteacher from Parramatta. Married Robert Kelly in 1957 and raised two children in Mosman, Sydney.",
    },
    # Kelly Gen 5
    {
        "key": "michael",
        "name": "Michael Robert Kelly",
        "birth": dt(1958, 5, 14),
        "death": dt(2019, 11, 28),
        "voice_gender": "male",
        "desc": "Architect and heritage restoration expert. Son of Robert and Patricia Kelly. Led several landmark Sydney restoration projects.",
    },
    {
        "key": "catherine",
        "name": "Catherine O'Neill Kelly",
        "birth": dt(1960, 10, 3),
        "death": None,   # alive
        "voice_gender": "female",
        "desc": "Journalist and author. Married Michael Kelly in 1984. Currently lives in Mosman, Sydney, and continues to write.",
    },
    # Kelly Gen 6 – living
    {
        "key": "sarah",
        "name": "Sarah Elizabeth Kelly",
        "birth": dt(1985, 4, 17),
        "death": None,  # alive
        "voice_gender": "female",
        "desc": "Marine biologist at CSIRO, Sydney. Daughter of Michael and Catherine Kelly. Studies coral reef ecosystems on the Great Barrier Reef.",
    },
    {
        "key": "daniel",
        "name": "Daniel James Kelly",
        "birth": dt(1988, 9, 2),
        "death": None,  # alive
        "voice_gender": "male",
        "desc": "Software engineer at a Sydney fintech startup. Son of Michael and Catherine Kelly. Passionate about open-source software and Irish history.",
    },
    # Anderson Gen 3 – William and Agnes's son (brother of Helen)
    {
        "key": "george",
        "name": "George William Anderson",
        "birth": dt(1900, 6, 15),
        "death": dt(1965, 4, 10),
        "voice_gender": "male",
        "desc": "Son of William and Agnes Anderson. Served with the AIF in North Africa 1941-43. Later a mathematics teacher at Sydney Boys High School.",
    },
    {
        "key": "margaret",
        "name": "Margaret Fraser Anderson",
        "birth": dt(1904, 2, 28),
        "death": dt(1985, 7, 19),
        "voice_gender": "female",
        "desc": "Bookkeeper and community volunteer. Married George Anderson in 1928. Raised Ian in the Neutral Bay terrace house with quiet determination.",
    },
    # Anderson Gen 4
    {
        "key": "ian",
        "name": "Ian George Anderson",
        "birth": dt(1932, 11, 7),
        "death": None,   # alive
        "voice_gender": "male",
        "desc": "Retired civil engineer. Son of George and Margaret Anderson. Helped build sections of the Sydney Harbour Tunnel. Lives in Manly, NSW.",
    },
    {
        "key": "evelyn",
        "name": "Evelyn Parker Anderson",
        "birth": dt(1935, 3, 19),
        "death": None,   # alive
        "voice_gender": "female",
        "desc": "Retired hospital administrator. Married Ian Anderson in 1960. Active in the Sydney Scottish community and Highland dance association.",
    },
]

# ── EXTENDED MEMORIES (additional, for all existing + all new memorials) ──────
EXTRA_MEMORIES = {
    # ── SEAN (add 8 more, total → 13) ────────────────────────────────────────
    "Sean Patrick Kelly": [
        (
            "Ah Fong and the silence",
            "Ah Fong was a quiet man in a city of shouters. He showed me that gold panning was "
            "a conversation with the river, not a fight. You tilt the pan, let the water decide, "
            "watch for the gleam at the bottom. I used that patience in everything afterward — "
            "in the grocery trade, in arguments with Brigid, in raising Thomas. "
            "I owe more to Ah Fong than he ever knew.",
        ),
        (
            "Thomas's first steps in the shop",
            "When Thomas was twelve I brought him to the shop on Collins Street and put him "
            "behind the counter. He was afraid of the customers and over-polite. By fourteen "
            "he was arguing with them about the price of tea. That was the day I knew "
            "he would be all right in the world. He had his mother's tongue and my stubbornness.",
        ),
        (
            "The bush fires, summer 1898",
            "The fire came down from the Dandenongs in a north wind so hot the birds fell from the trees. "
            "We wet the weatherboards with bucket chains and waited. The neighbours to the east lost "
            "their barn. We lost only the back fence. Brigid sat on the front step all night "
            "with a damp cloth over her face and did not once suggest we run.",
        ),
        (
            "The Claddagh ring",
            "My mother's Claddagh ring came to me at Cork docks, went into every goldfield I worked, "
            "crossed to New Zealand and back, and ended up on the mantelpiece in Footscray. "
            "When Thomas married Rose in 1896 I put it in his hand. "
            "I told him: the hands are for friendship, the crown for loyalty, the heart for love. "
            "Keep all three. He did.",
        ),
        (
            "Letters from Ireland",
            "For thirty years I wrote to my sister Nora in Skibbereen every Christmas. "
            "Her letters took four months to arrive and were always shorter than mine. "
            "She died in 1906 and I never met her children. "
            "By then Australia was more home to me than anywhere. But the loss sat heavily, "
            "and I kept her last letter in my Bible until I died.",
        ),
        (
            "Duncan Anderson — a neighbour of sorts",
            "I met Duncan Anderson once at a Federation dinner in Melbourne, 1901. "
            "He had come down from the Flinders Ranges for the occasion. "
            "A big, deliberate man — Scots to the bone, but with twenty years of Australian sun "
            "in his face. We talked about sheep, about land, about what the new Commonwealth meant. "
            "Neither of us imagined our grandchildren would share a roof one day.",
        ),
        (
            "The year I turned seventy",
            "My seventieth birthday was a Sunday in March 1912. Thomas and Rose came with James, "
            "still a boy then, full of energy. Brigid made a sponge cake with icing that "
            "read 'Sean 70' in lopsided letters. I sat on the verandah and thought: "
            "six thousand miles from Cork, four children raised, a house I built with my own hands. "
            "It was more than any young man on those docks could have imagined.",
        ),
        (
            "Last words for Thomas",
            "In the autumn before I died I called Thomas to the verandah and told him three things: "
            "honour your contracts, never borrow what you cannot repay, and be kinder to Rose "
            "than you think necessary. He laughed at the last one. I told him I was serious.",
        ),
    ],

    # ── BRIGID (add 8 more, total → 12) ──────────────────────────────────────
    "Brigid O'Brien Kelly": [
        (
            "Cork before I left",
            "In Skibbereen we still talked about the Famine as though it were yesterday, "
            "because for our parents it was yesterday. I grew up knowing what empty felt like. "
            "That knowledge shaped everything — how I kept the pantry, how I raised the children, "
            "how I refused to waste a crust. Australia was abundance. I never stopped being grateful.",
        ),
        (
            "The Irish women of Ballarat",
            "Moira Brennan, Eileen Doyle, Mrs Hogan from Tipperary — we were all the same: "
            "women who had crossed twelve thousand miles and were now building Ireland "
            "in a place that smelled of eucalyptus instead of peat. "
            "We shared recipes and gossip and sorrows in equal measure. "
            "I missed those women every day after we moved to Melbourne.",
        ),
        (
            "Thomas marrying Rose",
            "Rose Whitfield was not what I expected. She was English — which in my experience "
            "meant reserved — but she walked into Thomas's shop and argued with him in front of customers "
            "and I thought: well. That one will give him everything he needs and some things he doesn't. "
            "I was right. She was the backbone of that household. I told her so, eventually.",
        ),
        (
            "Sean panning for gold",
            "Sean used to demonstrate his gold panning technique to the children at the kitchen table "
            "using a mixing bowl and pebbles from the garden. He would tilt the bowl this way and that "
            "and say 'watch for the colour, watch for the gleam.' "
            "It was completely useless as a kitchen demonstration. The children loved it.",
        ),
        (
            "James going to war",
            "When James enlisted in 1940 I was already seventy-two. Sean had been dead twenty-two years. "
            "I thought: not again. Not another generation of boys sent to die in someone else's war. "
            "But James had his grandfather's stubbornness and his father Thomas's sense of duty. "
            "He came back. Not all boys come back. I prayed every day.",
        ),
        (
            "The verandah in old age",
            "My last years I spent mostly on the verandah watching the street. "
            "Footscray had changed — more Italians, fewer Irish, motor cars instead of horses. "
            "The world had moved on and taken me with it, which is better than the alternative. "
            "Thomas visited every Sunday with Rose. Robert, their grandson, used to sit on my knee "
            "and demand stories. I told him about Cork and the ships and the mud in Ballarat. "
            "He listened with his whole face.",
        ),
        (
            "The soda bread tradition",
            "I taught Rose to make soda bread the Cork way: buttermilk, not milk; caraway seeds; "
            "crossed on top before baking to let the fairies out. Rose made it every St Patrick's Day. "
            "She taught the recipe to Helen, who taught it to Robert, who made it for his children. "
            "By the time Michael was old enough to bake, the recipe was sixty years from Cork "
            "and still tasted like home.",
        ),
        (
            "A letter to Nora",
            "I wrote to Sean's sister Nora in Skibbereen for thirty years alongside him. "
            "After Sean died I continued writing — to her children, then to their children. "
            "The letters took months and the handwriting got worse and I wrote them anyway. "
            "The connection mattered more than the penmanship.",
        ),
    ],

    # ── THOMAS (add 7 more, total → 12) ──────────────────────────────────────
    "Thomas Michael Kelly": [
        (
            "My father's shop, before mine",
            "Before I had my own shop I worked behind my father Sean's counter in Footscray, "
            "learning the arithmetic of margins and the art of not short-measuring flour. "
            "Sean was harder on me than on any other employee. "
            "I understood why only after I hired my own first apprentice.",
        ),
        (
            "The refrigerated cabinet",
            "In 1910 I installed one of the first mechanical refrigeration units in a Melbourne shop. "
            "My competitors called it an extravagance. My customers called it a miracle. "
            "On the first hot summer day the cabinet paid for itself in butter that didn't melt. "
            "Rose had said: buy it. I had hesitated. Rose was right, as usual.",
        ),
        (
            "James learning to fly",
            "James sent me a postcard from Point Cook aerodrome: 'First solo today. "
            "The Tiger Moth goes where you tell it and sometimes where it wants.' "
            "I pinned that postcard to the back wall of the shop and read it every morning "
            "for five years. When he came home from New Guinea I took it down and gave it to him. "
            "He didn't know I'd kept it.",
        ),
        (
            "The Depression years",
            "The Depression hit the grocery trade hard. I extended credit to families I knew "
            "could not pay and kept no record of the debt on purpose. "
            "Rose managed the accounts and never once asked me to collect those debts. "
            "We came through thinner but intact. I am proud of those years more than the fat ones.",
        ),
        (
            "Meeting William Anderson in passing",
            "Rose and I visited Sydney once in 1925 to see James and Helen. "
            "Helen's father William Anderson took us to see the Harbour Bridge construction — "
            "just the caissons then, still going up from the shore. "
            "He knew every foreman and every rivet counter by name. "
            "A man who understood how things were built, from the ground up.",
        ),
        (
            "The Collins Street shop — last day",
            "I sold Kelly's Provisions in 1940, the year James went to war. "
            "The buyer was a Greek family, the Papadakis. Good people. "
            "I stood in the doorway one last time, smelling coffee and beeswax, "
            "forty-two years of mornings compressed into one minute. "
            "Then I put on my hat and walked home and didn't look back.",
        ),
        (
            "Advice to James before he married Helen",
            "Before James married Helen Anderson I told him one thing: "
            "she is cleverer than you and that is an advantage, not a threat. "
            "He looked at me blankly. That look told me he already knew. "
            "Good boy. He always had more sense than he let on.",
        ),
    ],

    # ── ROSE (add 8 more, total → 12) ────────────────────────────────────────
    "Rose Whitfield Kelly": [
        (
            "My father's garden in Adelaide",
            "Every variety of rose my father grew had a name and a history. "
            "He would walk the garden paths and tell me: this one came from an English cottage, "
            "this one grew over the trench at Ypres in some other war. "
            "I took that habit — naming things, remembering their provenance. "
            "Thomas said I applied it to people as well as plants. He was not wrong.",
        ),
        (
            "Arguing with Thomas about the refrigerator",
            "Thomas deliberated for six months about the refrigerated cabinet. "
            "I told him in April that butter did not keep in a Melbourne summer. "
            "He told me in June that the cost was prohibitive. "
            "I told him in August that the cost of rancid butter was also prohibitive. "
            "He bought it in September. We did not revisit the subject.",
        ),
        (
            "Helen Anderson the first time I met her",
            "James brought Helen Anderson to Collins Street in 1920, six weeks after they met. "
            "She walked into the shop, looked at the shelves, and said: "
            "'You're very well organised. The tea should be further from the flour.' "
            "I moved the tea the next morning. She noticed and said nothing. "
            "I knew right then she would do.",
        ),
        (
            "Teaching the children to read accounts",
            "Every child in my household could balance a ledger by the age of ten. "
            "I kept a household account book the same way Thomas kept the shop's — "
            "every shilling in, every shilling out. "
            "When Robert was learning, he asked why we wrote down the bread from Mrs Murphy "
            "who was not paid. I said: we write it so we remember to be grateful. "
            "He thought about that for a long time.",
        ),
        (
            "Agnes Anderson's nursing",
            "Agnes Brown Anderson — Helen's mother — was the most competent woman I ever knew. "
            "She managed a surgical ward the way I managed a household: no waste, no self-pity, "
            "everything in its place. We met three times in total. "
            "Each time I learned something I used for the rest of my life.",
        ),
        (
            "The war and the shop",
            "When James flew over New Guinea I kept a map on the kitchen wall and followed the campaigns. "
            "Thomas thought the map was morbid. I thought it was necessary. "
            "If your son is somewhere on earth, you should know where. "
            "He came home. The map stayed on the wall until the house was sold.",
        ),
        (
            "Robert's soda bread",
            "When Robert was seven, Brigid taught him to make soda bread. "
            "He burned the first two and ate the third one warm with too much butter, "
            "and declared it the best food he had ever tasted. "
            "He made it every St Patrick's Day for the rest of his life. "
            "I think he was doing it for Brigid, long after she was gone.",
        ),
        (
            "Thomas in his last years",
            "In his last years Thomas would sit in the garden and name the plants "
            "the way my father named his roses. He had never been a gardener — "
            "he had been a shopkeeper — but in old age he found the garden. "
            "I think it was something about watching things grow slowly. "
            "He had spent forty years in the world of quick returns. "
            "The garden was different. The garden was patient.",
        ),
    ],

    # ── JAMES (add 7 more, total → 12) ───────────────────────────────────────
    "James William Kelly": [
        (
            "My grandfather Sean's stories",
            "Brigid — my grandmother — used to tell Sean's stories better than Sean did. "
            "The Ballarat mud, Ah Fong and the silence, the Claddagh ring. "
            "I grew up knowing that our family had come from nothing and built something. "
            "That is not a small thing to know when you are young.",
        ),
        (
            "The Tiger Moth",
            "The Tiger Moth at Point Cook was a biplane built of fabric and optimism. "
            "It could stall if you looked at it wrong. My instructor was a former barnstormer "
            "who had survived thirty years of terrible decisions in the air. "
            "He told me: the plane wants to fly. Your job is to stop wanting to help it. "
            "Best flying instruction I ever received.",
        ),
        (
            "George Anderson — Helen's brother",
            "Helen's brother George Anderson was serving in North Africa while I was in New Guinea. "
            "We compared notes after the war over several whiskies at the Mosman RSL. "
            "George had been through Tobruk. I had been through Lae. "
            "Neither of us explained everything. There are things that fit in a room "
            "with another serviceman that fit nowhere else.",
        ),
        (
            "The radio silence over Lae",
            "Davies was on my left wing when the AA fire came up through the cloud. "
            "I heard his last transmission: 'Taking hits, starboard wing.' "
            "Then silence. I flew three more sorties that day. "
            "I have thought about the radio silence every year since. "
            "Every year I think: I should have said something back. "
            "There was nothing to say. There was nothing to say.",
        ),
        (
            "Helen's letters, read back",
            "Helen had written me a letter every week for five years of the war. "
            "She read them to me on the Mosman verandah when I came home — "
            "three evenings, two bottles of wine, the harbour going dark below us. "
            "She was matter-of-fact and funny and sometimes frightened, "
            "and she had hidden the fear between the practical lines "
            "so I would not worry. I worried anyway. I love her impossibly.",
        ),
        (
            "Robert at school",
            "Robert was the smartest boy in his class at Sydney Boys High, "
            "which he hid as thoroughly as he could. He helped the other boys with their maths "
            "and denied doing it. He had his mother's directness and my instinct for cover. "
            "I told him once: stop hiding what you're good at. "
            "He said: I'm not hiding it, I'm conserving it. "
            "I had no answer to that.",
        ),
        (
            "Qantas years and the planes I missed",
            "I instructed ground school for Qantas for twenty years after the war. "
            "I missed the flying every day. The cockpit smell, the physics of banking, "
            "the ground tilting away when you climb. "
            "Teaching kept me close enough. Not close enough, but close.",
        ),
    ],

    # ── DUNCAN (add 7 more, total → 12) ──────────────────────────────────────
    "Duncan Alasdair Anderson": [
        (
            "My father's croft",
            "The croft was twelve acres of thin soil on the edge of Loch Ness — "
            "beautiful and useless. We grew oats and kept four sheep. "
            "When the landlord raised the rent the third time my father told me "
            "plainly: there is nothing here for you. Go. "
            "I went. I took his silver watch and his advice and left Scotland "
            "at twenty-four and never returned.",
        ),
        (
            "The Aboriginal stockmen",
            "The Adnyamathanha men who worked our station knew the land in ways "
            "I was still learning after twenty years. They could read rain in a cloud "
            "three days out, find water in rock country where I saw nothing. "
            "Mungeranie — that was what they called the biggest man among them — "
            "saved two of my sheep in a gully flood that would have drowned them "
            "before I even knew they were missing.",
        ),
        (
            "Shearing season",
            "In the early years I sheared the flock myself: two hundred sheep, "
            "two weeks, bleeding hands every night. "
            "By 1880 we had enough acres to hire a team. "
            "I still worked alongside them on the first day of every season. "
            "A man who has forgotten what shearing feels like "
            "is a man who has forgotten what he is.",
        ),
        (
            "Flora's herb garden surviving the heat",
            "The South Australian summer would strip the skin off your knuckles. "
            "Temperatures past forty degrees for days running. "
            "Flora's herb garden from Inverness survived every summer for twenty years. "
            "She said the lavender was remembering the highlands. "
            "I said it was good Scottish stubbornness. We were both right.",
        ),
        (
            "William leaving for Sydney",
            "The day William loaded his bag onto the coach for Port Augusta "
            "I shook his hand and didn't trust myself to say more than two sentences. "
            "He had his mother's eyes and my jaw — the worst combination for looking at "
            "without emotion. Flora wept openly. "
            "I went back to the sheep. That evening she found me in the paddock "
            "and stood beside me without speaking. That was enough.",
        ),
        (
            "Letters from William in Sydney",
            "William wrote every two months as promised. His letters were full of the harbour — "
            "the light on the water, the size of the ships, the noise of the wharves. "
            "He had found his country. I was glad of it, even though my country "
            "was six hundred acres of red rock and saltbush, twelve hundred miles away.",
        ),
        (
            "Old age at the homestead",
            "My last years I spent mostly on the verandah watching the ranges. "
            "The colours changed every hour — red to purple to gold to black. "
            "I had built something on this land that had nothing when I arrived. "
            "Not rich. Not famous. But real. The stone homestead stood. "
            "Flora's herbs grew. The flock grazed. "
            "It was more than the croft by Loch Ness ever gave us.",
        ),
    ],

    # ── FLORA (add 8 more, total → 12) ───────────────────────────────────────
    "Flora Mackenzie Anderson": [
        (
            "My mother's garden in Inverness",
            "My mother grew herbs in a walled garden behind the cottage. "
            "Rosemary for remembrance — she said it every time she pruned it. "
            "I took cuttings wrapped in damp cloth on the ship to Adelaide. "
            "Three of the four survived. The rosemary bloomed in South Australia "
            "as if it had never known Scotland. I planted it by the homestead door "
            "and told it: this is home now. It agreed.",
        ),
        (
            "Teaching Agnes medicine",
            "Agnes — William's wife — trained as a nurse at Royal Prince Alfred. "
            "When she visited the homestead once with William I showed her "
            "what I knew of herbs for medicine. She was already better trained than I was, "
            "but she listened carefully and wrote everything down. "
            "A woman who listens even when she knows more — that is a rare woman.",
        ),
        (
            "The drought of 1884",
            "The 1884 drought was the worst in my memory on the station. "
            "The creek ran dry in March. Duncan moved the sheep forty miles "
            "to a neighbouring station's dam, which cost us dearly. "
            "I boiled seawater to wash the children — there was no other water for weeks. "
            "The drought broke in July. We lost thirty sheep. We kept everything else.",
        ),
        (
            "William's first job on the wharves",
            "William wrote to us from Sydney in 1888: 'I am loading wool bales at Circular Quay. "
            "The work is harder than shearing and twice as loud and I love it.' "
            "Duncan read the letter at the table and put it down and smiled "
            "at nothing in particular. That smile meant: my boy is all right.",
        ),
        (
            "Neighbours across the station",
            "The Patersons were twelve miles west of us, the Coopers fifteen miles east. "
            "We met at church in Hawker once a month and that was enough. "
            "In emergency — fire, flood, illness — we were on each other's doorsteps "
            "without being asked. That is what it means to live far from town. "
            "Your neighbour is your town.",
        ),
        (
            "George and Helen — our grandchildren",
            "William and Agnes's children came to visit the homestead once in 1906 — "
            "George was six and Helen was eleven. "
            "George ran straight to the sheep. Helen ran straight to my herb garden. "
            "I showed her the names: rosemary, thyme, feverfew. "
            "She repeated each name once and never forgot any of them. "
            "Agnes's child, through and through.",
        ),
        (
            "Duncan's last evening",
            "The evening before Duncan died he sat outside and watched the ranges go dark. "
            "He had not spoken much that week. I brought him tea and sat beside him "
            "and he said: 'Forty-eight years on this land and I still don't know its real name.' "
            "He meant the Adnyamathanha name. He had asked and never been given it. "
            "I held his hand. The stars came out. He was gone by morning.",
        ),
        (
            "Keeping the homestead after Duncan",
            "After Duncan died in 1910 I stayed at the homestead for three more years "
            "before William brought me to Sydney. I couldn't leave immediately. "
            "The place was too full of him. "
            "I kept the herb garden going. I kept the sheep logs. "
            "I kept his silver watch wound on the mantelpiece. "
            "When I finally left, I took a cutting of the rosemary. Of course I did.",
        ),
    ],

    # ── WILLIAM (add 7 more, total → 11) ─────────────────────────────────────
    "William Duncan Anderson": [
        (
            "Leaving the Flinders Ranges",
            "I left the station at twenty-three with my father's watch and my mother's blessing. "
            "The coach to Port Augusta took two days on corrugated tracks. "
            "Adelaide, then the train to Sydney. When I saw the harbour for the first time "
            "from the ferry, I knew I would never go back to red rock and saltbush. "
            "I wrote my father a careful letter. He wrote back: good. "
            "That was enough.",
        ),
        (
            "My sister Helen and James Kelly",
            "When Helen brought James Kelly to Sunday dinner I assessed him the way "
            "a foreman assesses a new man: can he carry the load, does he look you in the eye, "
            "does he know what he doesn't know? "
            "James passed on all three. He was older than Helen and had already been through "
            "a world that had made him careful. I shook his hand and told him to take care of her. "
            "He said: she takes care of herself. Correct answer.",
        ),
        (
            "Circular Quay mornings",
            "At five in the morning the quay was alive with wool bales, timber, coal, "
            "flour in hundred-pound sacks. You could smell which ship was in by the cargo. "
            "I loved those mornings more than any comfort I've had since. "
            "Work that used your whole body. A sky full of gulls. "
            "The harbour going from black to grey to gold.",
        ),
        (
            "George growing up",
            "My son George had Agnes's precision and my love of big things. "
            "As a boy he built models of bridges in the kitchen with matchsticks. "
            "When he grew up he taught mathematics, which surprised no one. "
            "When war came he enlisted for North Africa. "
            "Agnes didn't argue with him. I understood why — I would have done the same.",
        ),
        (
            "Agnes managing the ward",
            "Agnes ran her surgical ward at Royal Prince Alfred "
            "the way I ran my crew at the wharf: no waste, no excuses, everything accounted for. "
            "The difference was that her mistakes cost lives and mine cost timber. "
            "I have always thought she was braver than me. She disagrees. "
            "She is still wrong.",
        ),
        (
            "The 1918 influenza and Agnes",
            "Agnes worked through the influenza of 1918 without stopping for three weeks. "
            "She came home each night grey with exhaustion and was back before dawn. "
            "I kept the house, kept George and Helen fed, and kept out of her way. "
            "She lost twenty-three patients in a fortnight. "
            "She said their names before she slept. Every night. For the rest of her life.",
        ),
        (
            "Watching the bridge from Circular Quay",
            "I watched the Harbour Bridge arch from 1924 to 1932 from my window. "
            "The two halves crept toward each other over eight years. "
            "I brought George to see the joining in 1930. He was thirty, already teaching. "
            "We stood on the wharf and watched the two arches meet in the middle of the sky. "
            "I told him: that is what mathematics looks like when it gets out of the classroom. "
            "He laughed and didn't disagree.",
        ),
    ],

    # ── AGNES (add 7 more, total → 11) ───────────────────────────────────────
    "Agnes Brown Anderson": [
        (
            "My father's farm in Goulburn",
            "I grew up on a mixed farm outside Goulburn — wheat, cattle, a kitchen garden. "
            "My mother kept the accounts and my father kept the land. "
            "I wanted to be neither. I wanted to be in a hospital, which in 1888 "
            "was something you had to explain carefully to a farming family in New South Wales. "
            "My father thought about it for a week and said: all right then. "
            "He was a man of sense, my father.",
        ),
        (
            "William at the wharf",
            "William Anderson smelled of salt and coal tar when I first met him "
            "at the church social in 1892. He had very large hands and a Scots directness "
            "that I found immediately comfortable. We talked for two hours about everything "
            "except nursing or wharves. "
            "He asked to walk me home. I let him. "
            "He proposed within the year. I accepted.",
        ),
        (
            "Raising George and Helen",
            "George was methodical from birth — lined up his toy soldiers by height. "
            "Helen was quick and went sideways at problems, the way water finds around rock. "
            "I tried to teach them both that being clever was a tool, not a trophy. "
            "Helen grasped this immediately and never mentioned it. "
            "George grasped it eventually. "
            "Good children. Both of them.",
        ),
        (
            "George and the war",
            "When George enlisted for North Africa in 1940 I did not try to stop him. "
            "A woman who has nursed through one war understands that men who want to enlist "
            "will enlist, and that making them argue about it only damages the parting. "
            "I gave him a first aid kit I packed myself and told him to stay warm and eat. "
            "He came back in 1943, thinner and quieter. He never described North Africa. "
            "I never asked. Some things you know better than to ask.",
        ),
        (
            "Helen meeting James",
            "James Kelly asked Helen to dance at the Town Hall in 1919. "
            "She told me about him the next morning: older, a pilot, too sure of himself. "
            "I said: and? She said: and interesting. "
            "I said: interesting is better than safe. "
            "She thought about that. She married him the following year.",
        ),
        (
            "The surgical ward in the influenza year",
            "In October 1918 I lost count of the hours I had been on ward. "
            "The nurses were exhausted. The doctors were exhausted. "
            "We ran out of camphor and used spirits of turpentine and carbolic. "
            "We washed linen by hand because the laundry was backed up for days. "
            "Twenty-three patients. I say their names still. I will always say their names.",
        ),
        (
            "William's last years and the harbour",
            "After William retired from the wharf we used to take the Manly ferry "
            "on Sunday mornings just to be on the water. "
            "He would stand at the bow and watch the bridge and the Opera House — "
            "he didn't live to see the Opera House finished, but he watched it start. "
            "He said: Sydney is the most alive city on earth. "
            "I thought: anywhere you are is alive to me. "
            "I didn't tell him that. I should have.",
        ),
    ],

    # ── HELEN (add 7 more, total → 12) ───────────────────────────────────────
    "Helen Margaret Anderson Kelly": [
        (
            "My mother Agnes and medicine",
            "My mother Agnes ran her surgical ward the way she ran everything: "
            "with complete precision and no tolerance for sentiment without action. "
            "Growing up with her I learned that caring and competence are not opposites. "
            "She would have made an excellent general. She said the same about me, "
            "which was the highest compliment she offered.",
        ),
        (
            "My father William and the harbour",
            "My father William took me to Circular Quay on Sunday mornings "
            "and showed me how to read the tide and name the ships by their flags. "
            "He loved the harbour the way my grandfather Duncan loved the Flinders ranges — "
            "completely and without needing to explain why. "
            "I inherited his love of water. I passed it to Robert.",
        ),
        (
            "George my brother",
            "My brother George was six years younger and considerably more patient than me. "
            "He would sit for hours with a mathematics problem where I would solve it in five minutes "
            "and move to the next one. He said: I'm not solving the problem, I'm understanding it. "
            "That distinction took me twenty years to appreciate. "
            "He went to North Africa in 1940. He came back in 1943. "
            "He taught mathematics at Sydney Boys High until he died in 1965.",
        ),
        (
            "James's letters from New Guinea",
            "James's letters from New Guinea were heavily censored. "
            "What remained was a record of weather, food and small absurdities. "
            "No war. The censor had removed it. "
            "I read the absurdities as his way of telling me he was still himself. "
            "The week his letters stopped coming I went to the church and sat quietly for an hour. "
            "Then I went home and wrote him anyway.",
        ),
        (
            "Robert at the Opera House opening",
            "Robert telephoned me from the Opera House steps on the 20th of October 1973. "
            "He said: Mum, you should be here. I said: I'm ninety-eight years old, Robert. "
            "He said: worth noting. How do you feel? "
            "I said: like someone who has seen Sydney go from trams to this. "
            "He laughed. He had his father's laugh. I love that laugh.",
        ),
        (
            "Brigid Kelly's soda bread",
            "James's grandmother Brigid taught me to make soda bread the Cork way "
            "in the winter of 1920. Buttermilk, caraway, crossed on top. "
            "She was seventy-two and still the quickest hands in the kitchen. "
            "She told me: the bread is a greeting. You offer it to whoever comes. "
            "I made it every St Patrick's Day for fifty-five years. "
            "Then Robert made it. Then Patricia made it.",
        ),
        (
            "Living alone after James",
            "After James died in 1968 I stayed in the Mosman house "
            "because every room held something of him. "
            "His pilot's photograph on the hall table. His garden roses by the gate. "
            "His radio — the old Bakelite one — still tuned to the ABC. "
            "Robert visited every week. Patricia brought food I didn't need and company I did. "
            "I stayed in that house until I was eighty, which was seven years after James. "
            "That was long enough.",
        ),
    ],

    # ── ROBERT (add 7 more, total → 12) ──────────────────────────────────────
    "Robert James Kelly": [
        (
            "Growing up in Mosman",
            "Mosman in the 1930s and 40s was gardens and harbour light and the smell of jasmine "
            "from every fence. We walked to the beach in summer and the ferry in winter. "
            "My father James worked for Qantas and smelled of engine oil and authority. "
            "My mother Helen was the one who ran the house and the neighbourhood "
            "and most of the street without anybody noticing.",
        ),
        (
            "Learning to sail with William Anderson",
            "Helen's father William — my grandfather — taught me to sail a dinghy "
            "on Sydney Harbour when I was nine. He was already in his seventies "
            "and moved through the boat with the ease of a much younger man. "
            "He told me: the harbour is never the same twice. I have watched it for forty years "
            "and it still surprises me. I understood that at nine. "
            "I have thought about it every year since.",
        ),
        (
            "Marrying Patricia",
            "Patricia Murphy walked into the Mosman library in 1955 and told the librarian "
            "the shelving system was wrong. I was working in a carrel nearby and looked up. "
            "She was absolutely correct about the shelving. "
            "I walked over and agreed with her. She looked at me as if I had made a reasonable choice. "
            "We married two years later at St Thomas's, Mosman. "
            "She was the best decision I ever made.",
        ),
        (
            "Michael and architecture",
            "Michael was drawing floor plans at the age of eight with a ruler and protractor. "
            "He went to architecture school at Sydney University and came back talking about "
            "heritage and preservation with the same passion that I had talked about property development. "
            "We argued about it across many Sunday lunches. "
            "He was right more often than I was. I told him so eventually.",
        ),
        (
            "Patricia's teaching career",
            "Patricia taught English at Mosman Primary for twenty-three years. "
            "She could tell by the third day of school which child was struggling to read "
            "and which was bored because the reading was too easy. "
            "She said: both are the same problem, different direction. "
            "I thought about that often in the property business — "
            "every difficult negotiation had that shape.",
        ),
        (
            "The family reunion, 1990",
            "In 1990 we gathered sixty-three members of the Kelly and Anderson families "
            "in Mosman Park. My mother Helen was ninety-five and stood up without notes "
            "and named every person there — their parents, grandparents, connections. "
            "We were all thunderstruck. Catherine — Michael's wife — was taking notes. "
            "Later she said: your mother has the most extraordinary memory I've ever encountered. "
            "I said: she has always kept a very accurate map of who belongs to whom.",
        ),
        (
            "Daniel and the family history",
            "My grandson Daniel became obsessed with the family history in his twenties. "
            "He built a database of every Kelly and Anderson he could find — "
            "letters, shipping manifests, goldfield records. "
            "He found Ah Fong in a Ballarat census record from 1867, listed as a miner. "
            "He rang me at midnight from Sydney to tell me. "
            "I cried. I don't know exactly why.",
        ),
    ],
}

# ── NEW MEMORIAL MEMORIES ─────────────────────────────────────────────────────
NEW_MEMORIES = {
    "patricia": [
        (
            "Growing up in Parramatta",
            "Parramatta in the 1940s was still half country town — orchards along the river, "
            "cows in paddocks that are now shopping centres. "
            "My father was a plumber from Galway who played fiddle at the Irish club on Fridays. "
            "My mother was Parramatta-born and considered herself completely Australian "
            "while making soda bread every week and arguing about Irish politics at the dinner table. "
            "I grew up fluently bilingual in that particular contradiction.",
        ),
        (
            "Training as a teacher",
            "I trained at Sydney Teachers College in 1954. "
            "The education department in those days had precise ideas about what a woman teacher "
            "should be: measured, calm, unremarkable. "
            "I was two of those three things, which was two more than they expected. "
            "I loved teaching from the first day and never stopped loving it.",
        ),
        (
            "Meeting Robert at the library",
            "Robert Kelly agreed with me about the shelving system in the Mosman library "
            "without a moment's hesitation. "
            "Most men argue first and consider later. "
            "He considered first and agreed when he had. "
            "That told me something useful immediately. "
            "We talked for an hour about books and the Harbour Bridge and he asked if I "
            "wanted to walk along the foreshore. I said yes. Two years later, St Thomas's.",
        ),
        (
            "Robert's property work",
            "Robert developed property in the northern suburbs for thirty years. "
            "He built fibro houses in the early years and sandstone-and-recycled-timber houses "
            "later, after his mind changed about what a building should be. "
            "That change came from Michael — our son — who studied heritage architecture. "
            "I watched Robert change his mind because of Michael "
            "and felt very proud of both of them.",
        ),
        (
            "Raising Michael",
            "Michael drew floor plans from the age of eight. "
            "He built models of every significant Sydney building by age twelve. "
            "When he said he was applying to architecture school "
            "I telephoned Robert at his office and said: "
            "your son already knows what he is going to do. "
            "Robert said: good. I said: yes, good. "
            "It was good.",
        ),
        (
            "Michael and Catherine",
            "Catherine O'Neill walked into our house for the first time in 1983 "
            "and stood in the hallway looking at the prints on the wall. "
            "She said: are these your choices or Michael's? "
            "I said: both. She said: that's interesting. "
            "I immediately liked her. "
            "A woman who asks sharp questions and then pays attention to the answer — "
            "that is the kind of woman Michael needed.",
        ),
        (
            "Helen Kelly in her last years",
            "Helen — Robert's mother — lived to ninety-five in the Mosman house "
            "where James had planted roses by the gate. "
            "I visited her every Tuesday with food and conversation. "
            "She talked about James, about her father William and the harbour, "
            "about Agnes her mother who had nursed through two plagues and one war. "
            "I listened every week. "
            "Those conversations were an education I could not have gotten anywhere else.",
        ),
        (
            "Sarah and the ocean",
            "Sarah was born loving the water. "
            "By five she was swimming ahead of me at the beach. "
            "By twelve she was explaining tide patterns to her father. "
            "When she went to marine biology I thought: of course. "
            "Her great-great-grandfather William Anderson watched this harbour every morning "
            "for forty years. Something carries through.",
        ),
        (
            "Daniel and the family records",
            "Daniel built a database of every Kelly and Anderson he could trace. "
            "He found shipping manifests, mining records, hospital admission logs. "
            "He found a postcard from Thomas Kelly to Sean from 1910 "
            "in the Mitchell Library. "
            "He drove to Mosman to show us in person, which was the right choice. "
            "Robert looked at the postcard for a long time without speaking. "
            "Then he said: there he is.",
        ),
        (
            "Robert in his last years",
            "In his last years Robert sat in the garden the way his grandfather Sean "
            "had sat on the Footscray verandah — watching, not rushing. "
            "He had built things. He had raised good children. "
            "He had been married to me for forty-eight years, which he counted as his "
            "greatest project and his most successful one. "
            "He told me so plainly, which was Robert's way: plainly, once, meaning it completely.",
        ),
        (
            "Teaching reading",
            "The children who struggled to read were not stupid — they were misfitted. "
            "The system expected one speed and one method and most children fit neither. "
            "I spent twenty-three years finding the match between child and method. "
            "Every child who left my class reading fluently felt like a piece of engineering "
            "that worked. That is not a romantic thought. It is a precise one.",
        ),
        (
            "The soda bread",
            "I learned to make soda bread from Robert, who learned it from his grandmother Brigid "
            "via his mother Helen. Cork way: buttermilk, caraway, crossed on top. "
            "I made it every St Patrick's Day alongside Robert until he died. "
            "After he died I made it alone, which was a different thing "
            "but still the same bread.",
        ),
    ],

    "michael": [
        (
            "Growing up in Mosman, building models",
            "I grew up in the house my parents Robert and Patricia had on the escarpment in Mosman, "
            "looking down to the harbour. By eight I had built models of the Opera House, "
            "the Harbour Bridge and the Queen Victoria Building out of cardboard and matchsticks. "
            "My father thought it was a hobby. My mother told him: it's a direction. "
            "She was right, as she usually was.",
        ),
        (
            "Architecture school",
            "Sydney University architecture in the late 1970s was still dominated by the idea "
            "that new was better than old. I spent three years arguing with that assumption "
            "before I found a professor, Gertrude Marks, who agreed with me. "
            "She said: old buildings are not problems to solve. They are conversations to join. "
            "I have used that sentence in every presentation I gave for thirty years.",
        ),
        (
            "Meeting Catherine",
            "Catherine O'Neill was covering an architecture awards night for the Herald in 1983. "
            "She was taking notes in shorthand, which nobody used anymore, "
            "and asking questions that were better than the presenter's answers. "
            "I introduced myself and she said: I know who you are, I reviewed your Glebe project. "
            "I asked: favourably? She said: accurately. "
            "We had dinner three days later. I have never been bored since.",
        ),
        (
            "The Paddington terrace restoration",
            "My first major heritage project was a block of Paddington terraces "
            "that had been scheduled for demolition in 1986. "
            "I spent eight months arguing with the council and three months on the restoration. "
            "The ironwork went back to the pattern of the 1880s originals. "
            "The sandstone was washed, not painted over. "
            "When the owners moved in they said: it feels like it knows where it is. "
            "That was exactly what I wanted.",
        ),
        (
            "Arguing with Robert about property",
            "Dad built fibro houses in western Sydney in the 1960s. "
            "He was proud of them — affordable, solid, necessary. "
            "I told him: they're not nothing, but they're not conversation either. "
            "He said: not everything needs to be a conversation. "
            "We argued this across many Sunday lunches until he changed his mind "
            "somewhere around 1988. Then he started using recycled sandstone. "
            "He never explicitly conceded the argument. But the sandstone said it for him.",
        ),
        (
            "Sarah and the reef",
            "Sarah told us at fifteen that she was going to study the reef. "
            "Not marine biology in the abstract — the Great Barrier Reef specifically, "
            "because it was disappearing and she intended to stop it. "
            "She said this as a statement of fact, not ambition. "
            "Catherine looked at me across the table. I looked back. "
            "We were both thinking: where did she get that certainty? "
            "Then we both knew: from Patricia. From Robert. From further back.",
        ),
        (
            "Daniel at the keyboard",
            "Daniel built his first computer at fourteen from parts he bought at the markets. "
            "He and I argued about whether technology was architecture. "
            "He said: architecture is structure and function. Computers have both. "
            "I said: architecture has memory — it holds the marks of who used it. "
            "He thought for a week and came back and said: "
            "so does code, if you write it well. "
            "I had to give him that one.",
        ),
        (
            "The Rocks precinct project",
            "The Rocks restoration was the biggest project I led: "
            "fourteen warehouses from the 1820s to the 1880s, different limestone, "
            "different ironwork, different problems. "
            "We worked for six years. "
            "Catherine wrote the interpretive text for the heritage signage. "
            "Seeing her words on the wall next to my buildings — "
            "that was a particular happiness.",
        ),
        (
            "Helen Kelly — my great-grandmother",
            "I met my great-grandmother Helen Kelly once when I was eleven. "
            "She was eighty-three, completely sharp, sitting in the Mosman house "
            "surrounded by photographs of James in his RAAF uniform. "
            "She told me about the harbour of her childhood — the ferry captains, "
            "the smell of wool bales at Circular Quay, her father William's hands. "
            "I have thought about that afternoon many times. "
            "A direct line from Sydney 1900 to Mosman 1969, in one conversation.",
        ),
        (
            "Working with Catherine",
            "Catherine and I collaborated on projects for thirty years: "
            "she wrote the heritage reports and public histories, I did the physical restoration. "
            "We disagreed on methodology often and almost never on outcome. "
            "She said: you think in stone, I think in stories. "
            "I said: buildings are stories in stone. "
            "She said: now you're being a journalist. "
            "We both laughed. That's thirty years in one exchange.",
        ),
        (
            "A note to Sarah and Daniel",
            "I want Sarah and Daniel to know: "
            "the work is not what you make, it's what you make possible. "
            "The Paddington terraces were not about me. The Rocks project was not about me. "
            "They were about the people who would live and work there after me. "
            "Architecture is an argument that the future will use. "
            "Make it a good one. Make it honest. Make it last.",
        ),
    ],

    "catherine": [
        (
            "Journalism school, the Sydney Morning Herald",
            "I started at the Herald in 1984, covering arts and architecture. "
            "My editor said: architecture is not front page. "
            "I said: it is when someone is about to knock down 1820 sandstone for a carpark. "
            "He printed my story on page three. The carpark was not built. "
            "I understood something useful that day about what journalism is for.",
        ),
        (
            "Meeting Michael at the awards night",
            "Michael Kelly introduced himself at an architecture awards ceremony in 1983. "
            "He asked if my review of his Glebe project had been favourable. "
            "I said: it had been accurate. He looked at me for a moment. "
            "Then he said: accurate is better. "
            "I thought: this one understands how things work. "
            "Dinner three days later. I have been paying attention to him ever since.",
        ),
        (
            "Robert and Patricia Kelly",
            "Michael's parents Robert and Patricia were the most complementary pair I'd encountered. "
            "Robert thought in concrete and returns. Patricia thought in people and long time. "
            "Together they had raised Michael, which told you everything. "
            "Robert told me once: Catherine, you ask better questions than most architects I know. "
            "I told him: Michael taught me to look at structure. "
            "He laughed. He was proud of Michael in a way that required no statement.",
        ),
        (
            "The heritage writing",
            "For thirty years I wrote the historical and interpretive text for Michael's restoration projects. "
            "Each building had a story before it was his to restore. "
            "My job was to find those stories: in shipping records, census data, "
            "council minutes, newspaper archives. "
            "I wrote the first draft of the Rocks heritage report in six weeks "
            "and Michael read every page and argued with the chronology of three sentences. "
            "He was right about two of them.",
        ),
        (
            "Sarah choosing marine biology",
            "When Sarah said at fifteen she was going to study the reef I felt the clarity "
            "of someone who has found their direction. "
            "I had that at fifteen also — I was going to write, specifically and always. "
            "I told her: the decision is made, the path is not. Be patient with the path. "
            "She listened the way she always listened: completely, without interrupting, "
            "and then went and did exactly what she intended.",
        ),
        (
            "Daniel and the family database",
            "Daniel spent three years building a digital archive of the Kelly and Anderson families: "
            "shipping manifests, Ballarat mining records, hospital registers, letters. "
            "He found Sean Kelly in the Ballarat census of 1867. "
            "He found Agnes Anderson's nursing registration from 1890. "
            "He found a photograph of Duncan Anderson's homestead in a South Australian archive. "
            "He presented it all in a website he built himself. "
            "Michael cried. I took notes, which is my version of crying.",
        ),
        (
            "Michael and the Rocks project",
            "The Rocks was six years of Michael's life. "
            "I watched him study the limestone, argue with the council, "
            "brief the stone masons in the courtyard with a precision that was almost musical. "
            "When the project was finished and the heritage signage went up — "
            "my words on his stones — he said: that's what I wanted. "
            "That was enough. We walked home along the harbour. "
            "It was a good evening.",
        ),
        (
            "Ian and Evelyn Anderson",
            "We visited Ian and Evelyn Anderson in Manly in 2001 — "
            "Ian is George Anderson's son, cousin to Helen, which connects the Anderson line "
            "forward into the living world. "
            "Ian sat with Daniel for two hours over lunch telling him about George "
            "and the mathematics teaching and the North Africa years. "
            "Daniel recorded everything with his phone. "
            "That recording is now in the family archive. "
            "Ian didn't know he was doing something permanent. He was.",
        ),
        (
            "After Michael",
            "After Michael died in 2019 I continued writing. "
            "The heritage reports, the family archive, the book about the Rocks project "
            "that we had planned together and that I finished alone. "
            "Writing is how I locate myself. Without it I would be simply lost. "
            "Michael knew this. He used to bring me tea without being asked "
            "when I was working, and leave again without saying anything. "
            "That was his version of collaboration. I miss it every morning.",
        ),
        (
            "A letter to Sarah and Daniel",
            "To Sarah and Daniel: you came from people who built things. "
            "A stone homestead in the Flinders Ranges. Wharves at Circular Quay. "
            "A surgical ward through the influenza. Houses in Mosman. "
            "Your father restored the buildings that held those stories. "
            "You will do something I can't predict, in a world I can't imagine. "
            "Do it with the same care. That is the inheritance.",
        ),
    ],

    "sarah": [
        (
            "First swim at Balmoral",
            "My earliest memory is the water at Balmoral Beach, cold and green, "
            "and my father Michael holding my hands while I floated. "
            "He let go before I knew he had. "
            "I swam to the buoy and back, six years old, and came out "
            "already knowing the harbour was mine. "
            "Great-great-grandfather William Anderson would have understood that entirely.",
        ),
        (
            "The family archive and Ah Fong",
            "Daniel found Sean Kelly's name in the Ballarat census of 1867, "
            "two claims over from a man listed as 'Ah Fong, miner, China.' "
            "Mum found the newspaper account of their claim. "
            "Dad found the date Sean filed his land title in Footscray. "
            "I found the creek on a geological survey map. "
            "We are very good at research in this family. "
            "I wonder where that came from.",
        ),
        (
            "Choosing marine biology",
            "I told my parents at fifteen that I was going to study the Great Barrier Reef "
            "because it was bleaching and someone needed to stop it. "
            "Mum said: the decision is made, be patient with the path. "
            "Dad said: what do you need? "
            "Grandma Patricia sent me a book about coral ecology "
            "with a card that said: 'The reef needs someone like you. Go.' "
            "I went.",
        ),
        (
            "CSIRO fieldwork on the reef",
            "The reef at dawn is the most alive thing I have ever seen. "
            "Parrotfish and wrasse and the impossible colour of healthy coral. "
            "And the bleached sections — white as bone, perfectly dead. "
            "Every dive is a record. Every dive is evidence. "
            "I have dived the same transects for eight years and watched them change. "
            "That change is why I do this work.",
        ),
        (
            "Dad and the buildings",
            "My father Michael spent his life restoring old buildings. "
            "I asked him once why old things were worth saving. "
            "He said: because they carry evidence of how people solved problems. "
            "Every restoration is an act of listening. "
            "I do the same with coral cores — I drill and read and listen. "
            "A reef core is a hundred years of ocean chemistry "
            "laid down in calcium carbonate. That is a kind of building.",
        ),
        (
            "Grandma Catherine's archive",
            "Grandma Catherine built the family archive from shipping records and letters "
            "and census documents and photographs. "
            "She found Agnes Anderson's nursing registration from 1890 "
            "and Duncan Anderson's land grant in the Flinders Ranges. "
            "She showed me that finding things matters as much as making things. "
            "My fieldwork data is also an archive. Future scientists will read it. "
            "I try to be as careful as she is.",
        ),
        (
            "Ian Anderson in Manly",
            "Ian Anderson — Grandma Catherine's discovery, Dad's distant cousin — "
            "is ninety-three and still walks to the beach every morning in Manly. "
            "He told me about his father George teaching mathematics at Sydney Boys High, "
            "and his grandfather William watching the Harbour Bridge go up arch by arch. "
            "He said: your family has always watched things being built. "
            "I said: I watch things being unmade. I need to reverse that. "
            "He said: same skill, different direction.",
        ),
        (
            "The reef in ten years",
            "In ten years the section of reef I study will be unrecognisable "
            "if the ocean temperature keeps rising. "
            "This is not pessimism. It is measurement. "
            "My job is to document what is, understand the mechanism, and find the intervention. "
            "Brigid Kelly crossed the ocean in 1871 with two hundred people below decks "
            "and didn't turn back. Agnes Anderson nursed through the influenza without stopping. "
            "The bar for not stopping has been set fairly high in this family.",
        ),
        (
            "Daniel and the Kelly software",
            "Daniel built a tool to cross-reference historical records "
            "that my team at CSIRO now uses for tracking archival reef surveys. "
            "He built it in a weekend and explained it to me in ten minutes. "
            "I told him: you're wasted in fintech. "
            "He said: fintech pays for the tools that matter. "
            "He is not wrong. He is also clearly going to do something else eventually.",
        ),
        (
            "My father's note",
            "Dad left a note for Daniel and me in his desk when he died. "
            "He said: the work is not what you make, it's what you make possible. "
            "I read that note on the research vessel in the Coral Sea, "
            "the morning before a dive. "
            "The reef was at forty percent bleaching on the transect. "
            "I dived anyway. I recorded everything. I came back up. "
            "I think that is what he meant.",
        ),
    ],

    "daniel": [
        (
            "The first computer",
            "I built my first computer at fourteen from parts at the Paddy's Markets. "
            "My father Michael said: what is it for? "
            "I said: I don't know yet. "
            "He said: good answer. "
            "I think he was testing whether I needed permission or permission to explore. "
            "He gave me the second kind. That was what I needed.",
        ),
        (
            "The family database",
            "I started building the Kelly-Anderson database at twenty-two, "
            "after Grandma Patricia died and left me a box of letters and photographs. "
            "The box contained Sean Kelly's Ballarat claim ticket from 1866, "
            "a photograph of Flora Anderson in front of the Flinders homestead, "
            "and a postcard from Thomas Kelly to Sean from 1910. "
            "I digitised everything and kept going. "
            "I found Ah Fong in the census two claims from Sean. "
            "I rang Grandad Robert at midnight. He cried. I understand why now.",
        ),
        (
            "Coding and architecture",
            "Dad argued that architecture had memory — buildings hold the marks of use. "
            "I argued that well-written code has memory too. "
            "He thought for a week and came back and conceded the point, carefully. "
            "That was a very Michael Kelly concession: "
            "one week, carefully, not taking it back. "
            "I still think about that argument. "
            "The code I write is for systems that other people will use after me. "
            "I try to write comments as if they are heritage signage.",
        ),
        (
            "Sarah and the reef data",
            "Sarah's research team uses a tool I built for cross-referencing archival records. "
            "I built it for genealogy and she uses it for marine survey data. "
            "She said: the structure is the same — you're matching records across time. "
            "I said: I hadn't thought of it that way. "
            "She said: that's because you think in code and I think in transects. "
            "Same tool. She's using it better.",
        ),
        (
            "Meeting Ian Anderson",
            "Ian Anderson is ninety-three and still lives in Manly. "
            "We spent two hours over lunch and I recorded everything with my phone. "
            "He told me about his father George teaching mathematics after Tobruk; "
            "about his grandfather William's hands from the wharves; "
            "about his grandmother Agnes who said their names every night. "
            "He said: you should meet Evelyn, my wife. She remembers the Highland dances. "
            "I met Evelyn. She does. "
            "I now have audio of both of them.",
        ),
        (
            "Grandma Catherine's writing",
            "Catherine finished Dad's book about the Rocks project after he died. "
            "She sent me the manuscript. I read it in one sitting. "
            "It was accurate and warm and unsentimental and it made the buildings real "
            "the way Dad had made them physically real. "
            "I told her: this is the best thing you've written. "
            "She said: it's the hardest thing I've written. "
            "I said: same. She said: yes.",
        ),
        (
            "Robert Kelly's property empire",
            "Grandad Robert built houses in the northern suburbs for thirty years. "
            "He changed his mind about what a building should be "
            "sometime in the 1980s, partly because of Dad. "
            "He started using recycled sandstone and heritage detailing. "
            "The database I built shows a clear inflection in his project briefs "
            "between 1985 and 1990. "
            "Dad was arguing for five years before Robert moved. "
            "I showed Robert the graph two years before he died. "
            "He looked at it and said: the data is correct. "
            "That was his version of: you were right.",
        ),
        (
            "Agnes Anderson in the records",
            "I found Agnes Anderson Brown's nursing registration in the NSW health archives: "
            "22 February 1890, Royal Prince Alfred Hospital. "
            "There is a photograph — small, formal, ward sister's uniform, "
            "very straight posture, direct look. "
            "Sarah has the same look when she's working. "
            "I put the photograph in the archive and labelled it: "
            "'Agnes Brown Anderson, 1890. The look is inherited.'",
        ),
        (
            "The Kelly-Anderson archive",
            "The archive currently holds 847 records: "
            "letters, photographs, official documents, audio recordings, ship manifests. "
            "It goes from Sean Kelly's Ballarat claim in 1866 to Ian Anderson's voice "
            "recorded over lunch in Manly in 2024. "
            "158 years. Six families. One harbour. "
            "I'm not finished. I will keep going as long as there are records to find.",
        ),
    ],

    "george": [
        (
            "Growing up above Sydney Harbour",
            "My father William worked the Circular Quay wharves and our flat was in Neutral Bay, "
            "on the water side. I grew up watching the harbour from every window. "
            "My mother Agnes left for the hospital before I woke most mornings. "
            "My sister Helen and I walked to Neutral Bay Public School past the ferry wharves, "
            "and in summer we could see the Harbour Bridge going up arch by arch. "
            "It was an extraordinary thing to grow up watching.",
        ),
        (
            "Mathematics and the bridge",
            "When the Harbour Bridge arches met in the middle in 1930 "
            "my father took me to Circular Quay to watch. "
            "He shook hands with every man on his crew. "
            "I was thirty, already teaching. I understood the engineering better than he did "
            "and he understood the labour better than I did. "
            "Together, between us, we understood the whole bridge. "
            "I told him so. He laughed.",
        ),
        (
            "Enlisting for North Africa",
            "I enlisted in 1940 at forty years old. "
            "My mother Agnes did not argue. She gave me a first aid kit and instructions. "
            "My father William shook my hand and held it a moment longer than usual. "
            "Helen — my sister — was in Mosman with James Kelly, who was about to join the RAAF. "
            "Two Andersons and a Kelly going to war in the same year. "
            "My mother kept the map in her kitchen and moved pins.",
        ),
        (
            "Tobruk, 1941",
            "Tobruk in the siege of 1941 was heat and dust and the permanent sound of artillery. "
            "We were besieged for eight months. "
            "I taught the younger men in my section arithmetic for the gun ranges "
            "to keep them occupied between bombardments. "
            "When the siege broke I thought: if I survive this, I will teach mathematics "
            "for the rest of my life. That is what I did.",
        ),
        (
            "Coming home",
            "I came home from North Africa in 1943 thinner and quieter. "
            "Margaret was at the wharf with our son Ian, who was eleven. "
            "Ian looked at me as though performing a calculation. "
            "Then he said: Dad. "
            "That was correct. It was enough. "
            "We walked home along the harbour and I did not look back at the ship.",
        ),
        (
            "Sydney Boys High School",
            "I taught mathematics at Sydney Boys High from 1946 to 1965. "
            "The work was precise and useful and I loved it every year. "
            "I told the boys: mathematics is a language. "
            "It describes things that exist, things that might exist, and things that cannot. "
            "Your job is to know which is which. "
            "Some of them understood immediately. All of them learned eventually.",
        ),
        (
            "Margaret and the accounts",
            "Margaret kept accounts — for the house, for the school book fund, "
            "for the bush fire committee, for three other things simultaneously. "
            "She had a green ledger she carried everywhere. "
            "In twenty years I never found a mistake in it. "
            "I told her: you should have been an engineer. "
            "She said: I am an engineer. Of different systems. "
            "Correct.",
        ),
        (
            "Helen and James Kelly",
            "My sister Helen married James Kelly in 1920. "
            "James flew Kittyhawks over New Guinea while I was in North Africa. "
            "After the war we met at the Mosman RSL and compared notes carefully. "
            "Neither of us described everything. "
            "We both understood why the other didn't. "
            "James was a good man for my sister. She deserved that.",
        ),
        (
            "Ian at the engineering faculty",
            "Ian went to Sydney University to study civil engineering in 1952. "
            "He came home for dinner every Sunday while he was studying "
            "and argued with me about applied mathematics over the table. "
            "He said: pure maths is the theory; I want to build things. "
            "I said: you can't build things without the theory. "
            "He said: you can't teach the theory without the things. "
            "We were both right. He became an excellent engineer.",
        ),
        (
            "A note on teaching",
            "The best students I taught were not the fastest. "
            "They were the ones who understood that being wrong was information, not failure. "
            "Mathematics rewards those who revise. "
            "I tried to teach this by being wrong in front of the class "
            "at least once a fortnight, deliberately. "
            "After thirty years I was not always doing it deliberately. "
            "The lesson still held.",
        ),
    ],

    "margaret": [
        (
            "Growing up in Orange, NSW",
            "Orange in the early 1900s was a market town with apple orchards and cold winters. "
            "My father was a bank manager, careful with numbers. "
            "My mother kept the house accounts in a blue exercise book. "
            "I watched her and learned: a number is a fact. "
            "A column of numbers is an argument. "
            "An accurate column of numbers is an honest argument. "
            "I have worked with that principle all my life.",
        ),
        (
            "Bookkeeping in Sydney",
            "I moved to Sydney in 1924 and worked as a bookkeeper for a wool broker "
            "on Pitt Street for four years. "
            "In those years women bookkeepers were considered a curiosity. "
            "I kept the accounts accurately and quickly, "
            "which was the most effective response to being considered a curiosity.",
        ),
        (
            "Meeting George Anderson",
            "George Anderson was a mathematics teacher I met at the church social in 1927. "
            "He had been to Sydney University and back, and he talked about mathematics "
            "the way my father talked about interest rates: "
            "as though it were a set of tools for understanding reality. "
            "We married in 1928. In twenty-seven years of marriage "
            "we never once argued about arithmetic.",
        ),
        (
            "William Anderson — George's father",
            "William Anderson was a large, deliberate man who had worked the Sydney wharves "
            "for forty years. When I married George, William looked at me for a moment "
            "and said: can you keep accounts? I said: yes. "
            "He nodded and shook my hand. Agnes — George's mother — laughed and said: "
            "he approves of competence. I said: so do I. "
            "That was the beginning of a good understanding.",
        ),
        (
            "Agnes Anderson and the nursing",
            "Agnes Anderson was the most competent person I knew in fifty years of Sydney life. "
            "She had nursed through the influenza of 1918 and two smaller epidemics after. "
            "She managed her ward the way I managed the household accounts: "
            "precisely, without drama, with complete attention to what was in front of her. "
            "She taught me more about running a household than any book.",
        ),
        (
            "George going to North Africa",
            "George enlisted at forty. I did not argue. "
            "I had watched Agnes when James and George went to their respective wars "
            "and I had learned: a woman who argues with an enlistment "
            "loses the argument and damages the parting. "
            "I gave George his good boots, his warmest shirt, and the small accounts book "
            "I had used for our first year of marriage. "
            "He brought it back. It was in his breast pocket at Tobruk.",
        ),
        (
            "Raising Ian alone",
            "With George in North Africa from 1940 to 1943 I raised Ian alone. "
            "Ian was eight when George left. He was eleven when his father came home. "
            "In between he helped with the vegetable garden, the shopping, the accounts. "
            "He was a serious boy. He came home from school and sat with me at the kitchen table "
            "while I worked the ledger. He learned the ledger without being taught. "
            "That is Agnes's blood — the precision — coming through a generation.",
        ),
        (
            "George teaching mathematics",
            "George taught at Sydney Boys High for nineteen years after the war. "
            "He came home each evening with the same deliberate step. "
            "He ate dinner and marked homework and sometimes sat in the back garden "
            "working problems in a notebook. "
            "I did not interrupt those evenings. "
            "A man who has been through Tobruk and come out the other side "
            "to spend his life teaching mathematics — "
            "you do not interrupt that.",
        ),
        (
            "Ian and civil engineering",
            "When Ian said he was studying civil engineering I thought: "
            "his grandfather Duncan built a homestead in the Flinders Ranges, "
            "his grandfather William built wharves at Circular Quay, "
            "his father George built mathematical understanding in a hundred boys a year. "
            "All builders. Ian will build large things with concrete and steel. "
            "This is the family direction. "
            "I wrote that in the green ledger. I kept good records.",
        ),
        (
            "The green ledger",
            "I kept a green ledger for sixty years. "
            "It held every household account from 1928 to 1985: "
            "grocery bills, school fees, the repair of the front steps, "
            "George's textbooks, Ian's university fees, the painting of the kitchen. "
            "At the end of every year I ruled a line and balanced the column. "
            "Every year for sixty years the column balanced. "
            "I am prouder of that than of anything. "
            "Ian has the ledger now. I expect him to continue it.",
        ),
        (
            "Helen Kelly — George's sister",
            "Helen Anderson Kelly — George's sister — was the kind of woman you measured yourself against. "
            "She had raised a son through a depression and a war, "
            "written five years of weekly letters to a husband in New Guinea, "
            "and lived alone in the Mosman house until she was eighty. "
            "When I visited her in her last years we talked about Agnes, "
            "and about the harbour, and about what it meant to be a woman "
            "who had kept everything running while the men were elsewhere. "
            "She said: we were the structure. I said: yes. We were.",
        ),
    ],

    "ian": [
        (
            "Neutral Bay childhood",
            "I grew up in the Neutral Bay terrace where my parents George and Margaret Anderson lived. "
            "My father taught mathematics; my mother kept accounts. "
            "The house smelled of chalk and ledger paper. "
            "I walked to school along the foreshore and counted the ships in the harbour "
            "every morning as a kind of mathematics problem: "
            "how many, how big, where from. "
            "I have never stopped counting things.",
        ),
        (
            "When George came home from North Africa",
            "I was eleven when my father came home from the war in 1943. "
            "He was thinner and very quiet. "
            "I did not know what to say. I performed a small calculation: "
            "is this still my father, with adjustments, or is it a different man? "
            "Over three months I determined: same father, with new quietness. "
            "The quietness never entirely left. "
            "I learned to work beside it.",
        ),
        (
            "Engineering at Sydney University",
            "I studied civil engineering at Sydney University from 1952 to 1956. "
            "I argued with my father across dinner for four years about "
            "applied versus pure mathematics. "
            "He would not concede that pure mathematics needed the applied world. "
            "I would not concede that structure could exist without theory. "
            "We were both correct. We eventually told each other so, directly. "
            "That directness was the best thing he taught me.",
        ),
        (
            "The Sydney Harbour Tunnel",
            "I worked on the engineering team for the Sydney Harbour Tunnel from 1986 to 1992. "
            "My grandfather William Anderson had watched the Harbour Bridge go up from Circular Quay. "
            "I helped engineer the tunnel that went under the same water, sixty years later. "
            "He watched from above. I worked from below. "
            "I thought about him often. "
            "I wish I had told him about the tunnel project while he was alive.",
        ),
        (
            "Meeting Evelyn Parker",
            "Evelyn Parker was at a Highland dance evening at the Scottish Association in 1958. "
            "She danced with a precision and energy that was extraordinary and she knew every step. "
            "I am not a dancer. I told her so. "
            "She said: it's just applied geometry. "
            "I said: now you are speaking my language. "
            "We married two years later. "
            "She has been completely correct about applied geometry ever since.",
        ),
        (
            "My Aunt Helen Kelly",
            "My aunt Helen Anderson Kelly was a woman who had managed everything "
            "while the men in her family went to war — twice, if you count her husband James "
            "in New Guinea and her brother George in North Africa. "
            "I visited her in the Mosman house when I was young. "
            "She told me about Agnes and William and the harbour and the homestead in the Flinders. "
            "She had my grandmother Flora's habit of naming things so you remembered them. "
            "A direct line from Inverness to Mosman, in one woman.",
        ),
        (
            "Daniel Kelly and the archive",
            "Michael Kelly's son Daniel — Aunt Helen's great-grandnephew, "
            "which is a connection that only makes sense if you have Margaret's ledger to follow it — "
            "sat with me for two hours over lunch in Manly in 2024 "
            "and recorded everything I told him about George and Margaret and North Africa. "
            "He had already found Agnes's nursing registration and Duncan Anderson's land grant. "
            "He had found William Anderson in the 1910 harbour commission records. "
            "I told him: you have more of our family in that machine than in any room we've sat in. "
            "He said: that's the point.",
        ),
        (
            "Evelyn and the Scottish community",
            "Evelyn has kept the Sydney Scottish community alive through sheer determination "
            "for forty years. Highland dance evenings, Burns Night suppers, the St Andrew's dinner. "
            "My great-great-grandparents Duncan and Flora Anderson sailed from Scotland in the 1860s "
            "and never went back. "
            "Evelyn keeps Scotland present in Manly for people who have never seen it. "
            "I think Flora Anderson would have approved. "
            "I think she would have found the lavender.",
        ),
        (
            "Walking to the beach in Manly",
            "I walk to Manly Beach every morning. "
            "Ninety-three years old and I walk to the beach. "
            "The harbour is still there. The bridge is still there. "
            "My grandfather William watched this harbour for forty years. "
            "My grandfather Duncan watched the Flinders Ranges for forty years. "
            "I have watched this particular beach for sixty years. "
            "Long watching is a family habit. I recommend it.",
        ),
    ],

    "evelyn": [
        (
            "Growing up in Melbourne, the Highland dance",
            "My parents were both from Ayrshire, settled in Melbourne in the 1920s. "
            "My mother enrolled me in Highland dance at four and I have never stopped. "
            "It is applied geometry: angles, timing, precision under pressure. "
            "When I told Ian Anderson that at the dance evening in 1958 he said: "
            "now you are speaking my language. "
            "We were married two years later. The geometry continues.",
        ),
        (
            "Hospital administration",
            "I trained as a hospital administrator at St Vincent's in Sydney in the early 1960s. "
            "The job was the intersection of medicine, finance and human nature, "
            "which made it the most interesting work I could imagine. "
            "Agnès Brown Anderson — Ian's grandmother — had managed a surgical ward "
            "on three nurses and sheer competence. "
            "I managed a hospital department on budgets and systems. "
            "Different tools. Same essential task: make it work.",
        ),
        (
            "Meeting Ian's family",
            "Ian's father George Anderson died the year before we married. "
            "I knew him only from photographs and Margaret's descriptions. "
            "Margaret was meticulous: she told me about Tobruk and the mathematics teaching "
            "and the green ledger. "
            "She was a woman who believed that keeping good records was a form of respect. "
            "I agreed completely. I still do.",
        ),
        (
            "Margaret and the ledger",
            "Margaret Anderson kept a green household ledger from 1928 to 1985. "
            "When she died she left it to Ian with a note: continue it. "
            "Ian continued it for another twenty years. "
            "I have continued it since, which means the same household accounts "
            "have run without interruption for nearly a century. "
            "Agnes Anderson would have said: this is merely correct. "
            "Agnes Anderson was right.",
        ),
        (
            "The Sydney Scottish community",
            "I have run Highland dance evenings for the Sydney Scottish Association for forty years. "
            "The community is mostly third and fourth generation Australians "
            "who have never seen Scotland but for whom Scotland is still present — "
            "in the music and the steps and the food and the argument. "
            "Flora Mackenzie Anderson brought cuttings from Inverness to the Flinders Ranges in 1862. "
            "I bring the dances to Manly. It is the same impulse.",
        ),
        (
            "Ian and the Harbour Tunnel",
            "Ian helped engineer the Sydney Harbour Tunnel. "
            "He told me once that he thought about his grandfather William "
            "while working below the water that William had worked above. "
            "Ian said: he watched the bridge from the wharf. I worked under the harbour. "
            "Same water, different angle. "
            "I thought: every generation of this family finds a different way to be near the water.",
        ),
        (
            "Catherine Kelly and the archive",
            "Michael Kelly's wife Catherine came to Manly to research the family history "
            "for the archive her son Daniel was building. "
            "She sat in our kitchen and asked questions for three hours. "
            "She was the most precise interviewer I have encountered. "
            "I told her about the Highland dance evenings and Flora Anderson and the cuttings from Scotland. "
            "She wrote it down in shorthand. "
            "Daniel put it in the database. "
            "Flora Anderson is now in a digital archive in Sydney. "
            "I hope she would find that amusing.",
        ),
        (
            "Daniel and the database",
            "Daniel Kelly built a digital archive of the Kelly and Anderson families "
            "that now holds nearly a thousand records. "
            "He came to Manly with his phone and recorded Ian for two hours. "
            "I made tea and listened. "
            "Afterward Daniel showed us the archive on his laptop: "
            "photographs, letters, documents, audio. "
            "Ian found a photograph of his grandmother Margaret in the ledger records. "
            "He said nothing for a full minute. "
            "Then he said: she would have approved of the database. "
            "She would have checked the data.",
        ),
        (
            "Burns Night in Manly",
            "Every January we host Burns Night at our house: "
            "haggis, neeps, tatties, whisky, and the Address to a Haggis delivered by Ian "
            "in a Scottish accent that has improved in sixty years of practice. "
            "Ian's great-great-grandparents sailed from Scotland in the 1860s "
            "and never came back. "
            "We keep Scotland present for people who have never been. "
            "I think that is worth doing. "
            "I think Flora Anderson with her Inverness cuttings would agree.",
        ),
        (
            "A note on long marriages",
            "Ian and I have been married for sixty-five years. "
            "People ask: what is the secret? "
            "There is no secret. There is: "
            "keep accurate accounts — of money, of time, of gratitude. "
            "Do the applied geometry together. "
            "Keep the ledger. "
            "Walk to the beach. "
            "That is all. It is enough.",
        ),
    ],
}

# ── New relationships ─────────────────────────────────────────────────────────
# Format: (from_key, to_key, type)
# Keys mix existing ("robert","helen","william","agnes") and new
NEW_RELATIONSHIPS = [
    # Robert ↔ Patricia
    ("robert", "patricia", RelationshipType.SPOUSE),
    ("patricia", "robert", RelationshipType.SPOUSE),
    # Robert & Patricia → Michael
    ("robert", "michael", RelationshipType.PARENT),
    ("patricia", "michael", RelationshipType.PARENT),
    ("michael", "robert", RelationshipType.CHILD),
    ("michael", "patricia", RelationshipType.CHILD),
    # Michael ↔ Catherine
    ("michael", "catherine", RelationshipType.SPOUSE),
    ("catherine", "michael", RelationshipType.SPOUSE),
    # Michael & Catherine → Sarah
    ("michael", "sarah", RelationshipType.PARENT),
    ("catherine", "sarah", RelationshipType.PARENT),
    ("sarah", "michael", RelationshipType.CHILD),
    ("sarah", "catherine", RelationshipType.CHILD),
    # Michael & Catherine → Daniel
    ("michael", "daniel", RelationshipType.PARENT),
    ("catherine", "daniel", RelationshipType.PARENT),
    ("daniel", "michael", RelationshipType.CHILD),
    ("daniel", "catherine", RelationshipType.CHILD),
    # William & Agnes → George (Anderson Gen 3 sibling of Helen)
    ("william", "george", RelationshipType.PARENT),
    ("agnes", "george", RelationshipType.PARENT),
    ("george", "william", RelationshipType.CHILD),
    ("george", "agnes", RelationshipType.CHILD),
    # George ↔ Margaret
    ("george", "margaret", RelationshipType.SPOUSE),
    ("margaret", "george", RelationshipType.SPOUSE),
    # George & Margaret → Ian
    ("george", "ian", RelationshipType.PARENT),
    ("margaret", "ian", RelationshipType.PARENT),
    ("ian", "george", RelationshipType.CHILD),
    ("ian", "margaret", RelationshipType.CHILD),
    # Ian ↔ Evelyn
    ("ian", "evelyn", RelationshipType.SPOUSE),
    ("evelyn", "ian", RelationshipType.SPOUSE),
    # George ↔ Helen (siblings — same parents William+Agnes)
    ("george", "helen", RelationshipType.SIBLING),
    ("helen", "george", RelationshipType.SIBLING),
]


async def seed():
    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.id == 1).first()
        if not owner:
            print("⚠️  No user with id=1. Run the app once first.")
            return

        # ── 1. Create new memorials ─────────────────────────────────────────
        created: dict[str, Memorial] = {}

        # Load existing memorials by key so we can reference them in relationships
        key_to_name = {
            "sean": "Sean Patrick Kelly",
            "brigid": "Brigid O'Brien Kelly",
            "thomas": "Thomas Michael Kelly",
            "rose": "Rose Whitfield Kelly",
            "james": "James William Kelly",
            "helen": "Helen Margaret Anderson Kelly",
            "robert": "Robert James Kelly",
            "duncan": "Duncan Alasdair Anderson",
            "flora": "Flora Mackenzie Anderson",
            "william": "William Duncan Anderson",
            "agnes": "Agnes Brown Anderson",
        }
        for key, name in key_to_name.items():
            m = db.query(Memorial).filter(Memorial.name == name).first()
            if m:
                created[key] = m

        for m_def in NEW_MEMORIALS:
            key = m_def["key"]
            existing = db.query(Memorial).filter(Memorial.name == m_def["name"]).first()
            if existing:
                print(f"⏭️  Skipping {m_def['name']} (already exists id={existing.id})")
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

            access = MemorialAccess(memorial_id=memorial.id, user_id=1, role=UserRole.OWNER)
            db.add(access)
            db.commit()
            db.refresh(memorial)
            created[key] = memorial
            print(f"✅ Created: {memorial.name} (id={memorial.id})")

        # ── 2. Add extra memories for existing memorials ────────────────────
        for memorial_name, memory_list in EXTRA_MEMORIES.items():
            memorial = db.query(Memorial).filter(Memorial.name == memorial_name).first()
            if not memorial:
                print(f"  ⚠️  Memorial not found: {memorial_name}")
                continue
            await _add_memories(db, memorial, memory_list)

        # ── 3. Add memories for new memorials ───────────────────────────────
        key_map = {m_def["name"]: m_def["key"] for m_def in NEW_MEMORIALS}
        for memorial_name, memory_list in NEW_MEMORIES.items():
            memorial = created.get(memorial_name)
            if not memorial:
                # Try by name lookup using the key
                for m_def in NEW_MEMORIALS:
                    if m_def["key"] == memorial_name:
                        memorial = db.query(Memorial).filter(Memorial.name == m_def["name"]).first()
                        break
            if not memorial:
                print(f"  ⚠️  New memorial not found: {memorial_name}")
                continue
            await _add_memories(db, memorial, memory_list)

        # ── 4. Add new relationships ─────────────────────────────────────────
        for from_key, to_key, rel_type in NEW_RELATIONSHIPS:
            from_m = created.get(from_key)
            to_m = created.get(to_key)
            if not from_m or not to_m:
                print(f"  ⚠️  Skipping relationship {from_key} → {to_key}: memorial missing")
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
                print(f"  🔗 {from_m.name} --{rel_type.value}--> {to_m.name}")

        db.commit()
        print(f"\n✅ Done. EN memorials now: {db.query(Memorial).filter(Memorial.language == 'en').count()}")

    finally:
        db.close()


async def _add_memories(db, memorial: Memorial, memory_list: list):
    for title, content in memory_list:
        existing = db.query(Memory).filter(
            Memory.memorial_id == memorial.id,
            Memory.title == title,
        ).first()
        if existing:
            print(f"  ⏭️  '{title}' already exists for {memorial.name}")
            continue

        memory = Memory(
            memorial_id=memorial.id,
            title=title,
            content=content,
            source="seed",
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
            print(f"  📝 {memorial.name}: '{title}'")
        except Exception as e:
            db.rollback()
            print(f"  ❌ Embedding failed '{title}': {e}")
            memory = Memory(
                memorial_id=memorial.id,
                title=title,
                content=content,
                source="seed",
            )
            db.add(memory)
            db.commit()
            print(f"  📝 {memorial.name}: '{title}' (no embedding)")


if __name__ == "__main__":
    asyncio.run(seed())
