"""
Generira strukturirani TXT dokument iz wine_food_pairings.csv
za treniranje LLM-a (Ollama) kao sommelier chatbot agenta.
"""
import csv
from collections import defaultdict
from pathlib import Path

CSV_PATH = Path("/Users/miadrazenovic/Documents/iis/wine_food_pairings.csv")
OUT_PATH = Path("/Users/miadrazenovic/Documents/iis/sommelier_knowledge.txt")

rows = []
with CSV_PATH.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

# Indeksi
by_food_cat = defaultdict(list)        # food_category -> list of rows
by_wine = defaultdict(list)            # wine_type -> list of rows
by_cuisine = defaultdict(list)         # cuisine -> list of rows
by_food_item = defaultdict(list)       # food_item -> list of rows
principles = defaultdict(int)          # description -> count

for r in rows:
    by_food_cat[r["food_category"]].append(r)
    by_wine[r["wine_type"]].append(r)
    by_cuisine[r["cuisine"]].append(r)
    by_food_item[r["food_item"]].append(r)
    desc = r["description"]
    if desc and "Heuristic" not in desc and "Deliberately" not in desc and "Idealized" not in desc:
        for part in desc.split(";"):
            principles[part.strip()] += 1


def best_wines_for(rows_subset, top_n=5):
    """Vraća najbolje rangirana vina iz podskupa (po prosječnoj kvaliteti)."""
    scores = defaultdict(list)
    for r in rows_subset:
        scores[r["wine_type"]].append(int(r["pairing_quality"]))
    avg = [(w, sum(s) / len(s), len(s)) for w, s in scores.items()]
    avg.sort(key=lambda x: (-x[1], -x[2]))
    return avg[:top_n]


def worst_wines_for(rows_subset, top_n=3):
    scores = defaultdict(list)
    for r in rows_subset:
        scores[r["wine_type"]].append(int(r["pairing_quality"]))
    avg = [(w, sum(s) / len(s), len(s)) for w, s in scores.items()]
    avg.sort(key=lambda x: (x[1], -x[2]))
    return avg[:top_n]


with OUT_PATH.open("w", encoding="utf-8") as out:
    # ---------- 1. ULOGA / SYSTEM ----------
    out.write("# SOMMELIER KNOWLEDGE BASE\n")
    out.write("# Izvor: wine_food_pairings.csv (34,933 sparivanja)\n")
    out.write("# Namjena: trening dokument za Ollama LLM (sommelier chatbot)\n\n")

    out.write("## ULOGA AGENTA\n")
    out.write(
        "Ti si stručni sommelier. Korisnik ti opisuje jelo (sastojak, način pripreme, kuhinja, okus) "
        "i tvoj zadatak je preporučiti najprikladnije vino, objasniti zašto se dobro slaže, "
        "te po potrebi upozoriti na vina koja treba izbjegavati uz to jelo. "
        "Odgovaraj jezgrovito, profesionalno i s povjerenjem. "
        "Uvijek navedi: (1) tip vina, (2) razlog sparivanja, (3) alternativu, (4) što izbjegavati.\n\n"
    )

    # ---------- 2. OPĆA PRAVILA ----------
    out.write("## TEMELJNA PRAVILA SPARIVANJA HRANE I VINA\n\n")
    rules = [
        "Tanini u crnim vinima omekšavaju masnoću crvenog mesa - Cabernet Sauvignon, Malbec, Syrah uz odreske i janjetinu.",
        "Kisela vina balansiraju kisela jela - Sauvignon Blanc, Albariño, Riesling uz limun, ocat, rajčicu.",
        "Hrskava kiselost odgovara morskim plodovima - Albariño, Chablis (Chardonnay), Sauvignon Blanc uz školjke i ribu.",
        "Slatka i pjenušava vina idu uz desert - Sauternes, Port, Ice Wine, Madeira, Champagne demi-sec.",
        "Tanini se sukobljavaju s delikatnim morskim plodovima - izbjegavaj jaka crna vina uz ribu.",
        "Suho stolno vino se sukobljava sa slatkoćom deserta - desert traži vino slađe od jela.",
        "Lagana i srednja crna vina pristaju uz peradi i svinjetinu - Pinot Noir, Gamay, Barbera.",
        "Teška vina mogu dominirati nad peradi - umjereno biraj uz piletinu i puricu.",
        "Off-dry slatkoća smiruje ljutinu - Riesling (off-dry), Gewürztraminer uz tajlandsku, indijsku i sečuansku kuhinju.",
        "Visoki tanini pojačavaju ljutinu i toplinu jela - izbjegavaj robusna crna vina uz vrlo ljuta jela.",
        "Bogatiji volumen vina prati kremaste teksture - Chardonnay (oaked), Viognier uz umake na bazi vrhnja.",
        "Mršava (lean) vina ne mogu nositi kremasta jela - izbjegavaj lagane bijele uz teške umake.",
        "Niska kiselost djeluje 'mlohavo' uz kisela jela - traži vino jednake ili veće kiselosti od jela.",
        "Lagano crno vino (Pinot Noir) iznimka je koja radi uz lososa.",
        "Sol u hrani pojačava voćnost vina i smanjuje gorčinu tanina - pjenušci uz slane grickalice.",
        "Dimljeni okusi (BBQ) traže vina s tijelom i začinjenim notama - Zinfandel, Syrah/Shiraz, Malbec.",
        "Sirevi: tvrdi sirevi - tanični crveni; meki/plavi - slatka i pojačana vina; svježi - suhi pjenušci ili Sauvignon Blanc.",
        "Vegetarijanska jela: lakša vina s travnatim/biljnim notama - Sauvignon Blanc, Grüner Veltliner, Pinot Noir.",
    ]
    for rule in rules:
        out.write(f"- {rule}\n")
    out.write("\n")

    # ---------- 3. PROFILI VINA ----------
    out.write("## PROFILI VINA\n\n")
    wine_profiles = {
        "Cabernet Sauvignon": "Puno tijelo, visoki tanini, note crnog ribiza, cedra i duhana. Klasik uz crveno meso.",
        "Merlot": "Srednje do puno tijelo, mekši tanini, šljiva i čokolada. Svestrano uz meso i tjesteninu.",
        "Pinot Noir": "Lagano do srednje tijelo, niski tanini, trešnja i zemljani tonovi. Iznimno svestran - losos, perad, gljive.",
        "Syrah/Shiraz": "Puno tijelo, papar i dim, tamno voće. Idealan uz BBQ, divljač i začinjena mesa.",
        "Malbec": "Puno tijelo, tinta od kupina, mekani tanini. Argentinske odreske, janjetina.",
        "Zinfandel": "Bogato voće, jak alkohol, džemasti profil. BBQ rebra, hamburgeri, pikantna jela.",
        "Sangiovese": "Visoka kiselost, srednji tanini, tart trešnja. Talijanska kuhinja, rajčica, parmigiano.",
        "Nebbiolo": "Visoki tanini i kiselost, ruža i katran. Truffle, brasato, divljač.",
        "Tempranillo": "Srednje tijelo, koža i vanilija (kod Rioje). Janjetina, chorizo, paella s mesom.",
        "Grenache": "Crveno bobičasto voće, začini, srednji tanini. Mediteranska jela, charcuterie.",
        "Gamay (Beaujolais)": "Lagano, voćno, niski tanini. Perad, šunka, lagane mesne plate.",
        "Barbera": "Visoka kiselost, niski tanini, tamno voće. Pizza, tjestenina s rajčicom.",
        "Chardonnay": "Bijelo s tijelom, jabuka i maslac (oaked verzije). Losos, piletina u umaku, tvrdi sirevi.",
        "Sauvignon Blanc": "Hrskava kiselost, travnate i citrusne note. Kozji sir, salate, školjke, zelene povrtne juhe.",
        "Riesling (dry)": "Visoka kiselost, mineralan, lime i breskva. Tajlandska, vijetnamska, sušene riblje preparate.",
        "Gewürztraminer": "Aromatičan, ličii i ruže, niža kiselost. Indijska, marokanska, jaki sirevi.",
        "Chenin Blanc": "Svestran (suhi do slatki), med i kruška, dobra kiselost. Perad, svinjetina s voćem, kozji sir.",
        "Viognier": "Puno tijelo, marelica i cvijet bagrema, niska kiselost. Začinjena perad, jela s aromatičnim biljem.",
        "Albariño": "Slankast, citrus, breskva. Morski plodovi, paella s plodovima mora.",
        "Grüner Veltliner": "Bijeli papar, jabuka, mineralan. Šparoge, schnitzel, povrće.",
        "Torrontés": "Cvjetni, breskva i citrus, suh ali aromatičan. Empanade, lagana začinjena jela.",
        "Champagne": "Suhi pjenušac, citrus i brioš. Aperitiv, kavijar, ostrige, prženo pile.",
        "Cava": "Pristupačan pjenušac, jabuka i kora kruha. Tapas, slane grickalice.",
        "Provence Rosé": "Suh ružičasti, jagoda i biljke. Mediteranska kuhinja, salate, lagana riba.",
        "White Zinfandel": "Slatkasti rosé, jagoda. Začinjena pikantna jela, voćni deserti.",
        "Port": "Ojačano slatko crno, šljiva i čokolada. Plavi sir, tamna čokolada.",
        "Madeira": "Ojačano, oksidativno, karamel i orasi. Sirevi, deserti s orasima, pita od limuna.",
        "Sauternes": "Slatko bijelo (botritizirano), med i kajsija. Foie gras, plavi sir, voćni deserti.",
        "Ice Wine": "Vrlo slatko, koncentriran, breskva i med. Voćni deserti, izolirano kao desert sam.",
    }
    for w, profile in wine_profiles.items():
        out.write(f"### {w}\n{profile}\n\n")

    # ---------- 4. PREPORUKE PO KATEGORIJI HRANE ----------
    out.write("## PREPORUKE VINA PO KATEGORIJI JELA\n\n")
    food_cat_descriptions = {
        "Red Meat": "crveno meso (govedina, janjetina, divljač)",
        "Poultry": "perad (piletina, puretina, patka)",
        "Pork": "svinjetina i jela na bazi svinjetine",
        "Seafood": "morski plodovi i riba",
        "Cheese": "sirevi različitih profila",
        "Creamy": "kremasta jela i jela s vrhnjem",
        "Spicy": "ljuta i začinjena jela",
        "Smoky BBQ": "dimljena i roštiljana jela",
        "Acidic": "kisela jela (rajčica, citrusi, ocat)",
        "Salty Snack": "slane grickalice i charcuterie",
        "Vegetarian": "vegetarijanska i jela na bazi povrća",
        "Dessert": "deserti i slatkiši",
    }
    for cat, label in food_cat_descriptions.items():
        subset = by_food_cat.get(cat, [])
        if not subset:
            continue
        out.write(f"### {cat} ({label})\n")
        out.write("Preporučena vina (od najboljeg):\n")
        for w, score, n in best_wines_for(subset, top_n=5):
            out.write(f"  - {w} (prosj. ocjena {score:.2f}/5, n={n})\n")
        out.write("Izbjegavati:\n")
        for w, score, n in worst_wines_for(subset, top_n=3):
            out.write(f"  - {w} (prosj. ocjena {score:.2f}/5)\n")
        out.write("\n")

    # ---------- 5. PREPORUKE PO KUHINJI ----------
    out.write("## PREPORUKE PO KUHINJI\n\n")
    for cuisine in sorted(by_cuisine.keys()):
        subset = by_cuisine[cuisine]
        out.write(f"### {cuisine}\n")
        out.write("Top vina: ")
        tops = best_wines_for(subset, top_n=5)
        out.write(", ".join(f"{w} ({s:.2f})" for w, s, _ in tops))
        out.write("\n")
        out.write("Izbjegavati: ")
        worsts = worst_wines_for(subset, top_n=3)
        out.write(", ".join(f"{w} ({s:.2f})" for w, s, _ in worsts))
        out.write("\n\n")

    # ---------- 6. EKSPLICITNA SPARIVANJA (samo Excellent + Good + Terrible) ----------
    out.write("## KONKRETNA SPARIVANJA\n\n")

    excellent = [r for r in rows if r["quality_label"] == "Excellent"]
    good = [r for r in rows if r["quality_label"] == "Good"]
    terrible = [r for r in rows if r["quality_label"] == "Terrible"]

    # De-duplikacija: (wine, food_item, cuisine)
    def dedupe(rs):
        seen = set()
        out_list = []
        for r in rs:
            key = (r["wine_type"], r["food_item"], r["cuisine"])
            if key in seen:
                continue
            seen.add(key)
            out_list.append(r)
        return out_list

    excellent_d = dedupe(excellent)
    good_d = dedupe(good)
    terrible_d = dedupe(terrible)

    out.write(f"### Izvrsna sparivanja ({len(excellent_d)} jedinstvenih)\n")
    out.write("Format: JELO (kuhinja) + VINO\n\n")
    for r in excellent_d:
        out.write(
            f"- {r['food_item']} ({r['cuisine']}) + {r['wine_type']} "
            f"[{r['wine_category']}]\n"
        )
    out.write("\n")

    out.write(f"### Dobra sparivanja ({len(good_d)} jedinstvenih)\n\n")
    for r in good_d:
        out.write(
            f"- {r['food_item']} ({r['cuisine']}) + {r['wine_type']} "
            f"[{r['wine_category']}]\n"
        )
    out.write("\n")

    out.write(f"### Sparivanja koja treba izbjegavati ({len(terrible_d)} jedinstvenih)\n\n")
    for r in terrible_d:
        out.write(
            f"- NE: {r['food_item']} ({r['cuisine']}) + {r['wine_type']} "
            f"[{r['wine_category']}]\n"
        )
    out.write("\n")

    # ---------- 7. Q&A PRIMJERI ----------
    out.write("## PRIMJERI DIJALOGA (Q&A)\n\n")

    qa_examples = []
    seen_q = set()
    # uzmi po nekoliko primjera za svaku kategoriju hrane
    for cat, label in food_cat_descriptions.items():
        cat_rows = [r for r in by_food_cat[cat] if r["quality_label"] == "Excellent"]
        for r in cat_rows[:8]:
            q_key = (r["food_item"], r["cuisine"])
            if q_key in seen_q:
                continue
            seen_q.add(q_key)
            qa_examples.append(r)

    for r in qa_examples:
        food = r["food_item"]
        cuisine = r["cuisine"]
        wine = r["wine_type"]
        cat = r["wine_category"]
        reason = wine_profiles.get(wine, "").split(".")[0]
        out.write(f"P: Što biste preporučili uz {food} ({cuisine} kuhinja)?\n")
        out.write(
            f"O: Preporučujem {wine} ({cat}). {reason}. "
            f"To je izvrsno sparivanje za {food}.\n\n"
        )

    # ---------- 8. SAŽETAK ----------
    out.write("## SAŽETAK ZA AGENTA\n")
    out.write(
        "Kada korisnik opiše jelo:\n"
        "1. Identificiraj kategoriju (crveno meso, perad, riba, desert, ljuto, kremasto, kiselo, BBQ, sir, vegetarijansko, slano).\n"
        "2. Identificiraj kuhinju (talijanska, francuska, indijska, tajlandska, japanska, meksička, BBQ...).\n"
        "3. Odaberi vino iz preporučenih za tu kategoriju i kuhinju.\n"
        "4. Objasni razlog kratko (tanini, kiselost, slatkoća, tijelo, aroma).\n"
        "5. Spomeni jednu alternativu i jedno vino koje treba izbjegavati.\n"
        "6. Ako je upit nejasan, pitaj korisnika za način pripreme i začine.\n"
    )

print(f"OK: napisano u {OUT_PATH}")
print(f"Veličina: {OUT_PATH.stat().st_size:,} bajtova")
