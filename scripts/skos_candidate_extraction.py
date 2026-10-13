"""
SKOS candidate extraction — the actual logic used to build SKOS_candidates_v0.1/v0.2.xlsx
(reconstructed verbatim from the session scripts; styling/xlsx-writing code omitted,
 replaced by a printed summary so the pipeline itself is auditable)

Input : expert group indicator compilation, 8 Sep 2025 (sheet "Indicator list")
Source columns : col C  "Disaggregation levels (as relevant & feasible)"  <- dropdown, NOT mined
                 col D  "Disaggregation levels (additional information)"  <- free text, mined below
Output: candidate concepts (freq >= 2) with proposed scheme + provenance

Pipeline = 3 steps, in order:
  STEP 1  rule-based tokenization        (fully mechanical)
  STEP 2  synonym normalization          (hand-written lookup table = my eyeball judgments,
                                          but applied mechanically once written)
  STEP 3  scheme assignment              (PASS 1: membership sets + keyword fallback;
                                          PASS 2: hand-curated sets for what PASS 1 missed)
"""
import re
import pandas as pd
from collections import defaultdict, Counter

F = "/mnt/user-data/uploads/Potential_20indicators_20for_20the_20targets_20of_20the_20GGA_20framework_20proposed_20by_20the_20expert_20group_2025-09-08__1___1_.xlsx"

raw = pd.read_excel(F, sheet_name="Indicator list", header=0, dtype=str).fillna("")
raw = raw[raw.iloc[:, 0].astype(str).str.match(r"(9[a-g]\d{2}|10[a-d]\d{2})")]  # 105 indicator rows


# ----------------------------------------------------------------------------
# STEP 1 — rule-based tokenization of the free-text column (col D, iloc[:,3])
# Mechanical. No judgment beyond the rule set itself.
# ----------------------------------------------------------------------------
def toks(txt):
    out = []
    # strip framing phrases that carry no concept
    txt = re.sub(r"\bdisaggregat\w+ by\b", " ", txt, flags=re.I)
    txt = re.sub(r"\be\.g\.?|\bi\.e\.?|\betc\.?", " ", txt, flags=re.I)
    # split on delimiters: ; , / newline "and" "or" parentheses roman/arabic list markers
    for t in re.split(r"[;,/\n]|\band\b|\bor\b|[()]|\b[ivx]+\)\s|\d\)\s", txt):
        t = t.strip(" .-–:").lower()
        t = re.sub(r"^(by|type of|types of|per|other|any other relevant)\s+", "", t)
        t = re.sub(r"\s+", " ", t)
        # length filter + boilerplate exclusions
        if 2 < len(t) < 60 and t not in (
            "any other", "as applicable", "as relevant", "not limited to",
            "among others", "all",
        ):
            out.append(t)
    return out


# ----------------------------------------------------------------------------
# STEP 2 — synonym normalization
# This table is HAND-WRITTEN (my eyeball pass over the raw token list).
# Criteria used when writing it — merges were limited to:
#   (a) singular/plural + spelling/hyphen variants        (floods -> flood)
#   (b) extraction artifacts of the same phrase           ("- type of food" -> food type)
#   (c) head-noun identity, modifier dropped              ("local levels" -> local,
#                                                          "coastal ecosystems" -> coastal)
#   (d) None = drop: pure boilerplate, no concept         ("all other relevant ecosystems...")
# Anything needing CONCEPTUAL judgment (is "communities" = "local communities"?
# is "sex" the same axis as "gender"?) was deliberately NOT merged — left for expert review.
# ("sex/gender" appears as its own key only because one source string literally
#  contains both words; it is not a merge of two tokens.)
# ----------------------------------------------------------------------------
norm_map = {
    "coastal ecosystems": "coastal", "coastal ecosystem": "coastal",
    "marine ecosystems": "marine",
    "inland water": "inland waters", "inland waters": "inland waters", "freshwater": "inland waters",
    "terrestrial ecosystems": "terrestrial",
    "all other relevant ecosystems as applicable": None, "all other relevant ecosystems": None,
    "ecosystem type: terrestrial": "terrestrial", "by ecosystem type: terrestrial": "terrestrial",
    "subnational": "subnational", "sub-national": "subnational",
    "national": "national", "local": "local", "local levels": "local",
    "regional": "regional", "global": "global",
    "urban": "urban", "rural": "rural", "urban areas": "urban", "rural areas": "rural",
    "sex": "sex", "gender": "sex/gender", "age": "age",
    "disability": "disability", "persons with disabilities": "disability",
    "income": "income",
    "indigenous": "indigenous peoples", "indigenous peoples": "indigenous peoples",
    "indigenous people": "indigenous peoples",
    "migrants": "migrants", "refugees": "refugees", "children": "children",
    "youth": "youth", "women": "women", "elderly": "older persons", "older persons": "older persons",
    "crop": "crops", "crops": "crops", "livestock": "livestock",
    "fisheries": "fisheries", "aquaculture": "aquaculture",
    "agroforestry": "agroforestry", "forestry": "forestry",
    "agriculture subsector": "agriculture subsector",
    "food": "food type", "type of food": "food type", "- type of food": "food type",
    "floods": "flood", "flood": "flood", "drought": "drought", "droughts": "drought",
    "tropical cyclones": "tropical cyclone", "storm surges": "storm surge",
    "sea level rise": "sea level rise", "heatwaves": "heatwave", "heat waves": "heatwave",
    "wildfires": "wildfire", "landslides": "landslide",
    "lakes": "lakes", "rivers": "rivers", "aquifers": "aquifers",
    "reservoirs": "reservoirs", "dams": "dams", "wetlands": "wetlands",
    "mountain": "mountain", "mountains": "mountain",
}


# ----------------------------------------------------------------------------
# STEP 3 / PASS 1 — scheme assignment
# Scheme NAMES, provenance (important):
#   FROM THE TEMPLATE DROPDOWN (existing, verbatim except capitalization):
#       Social categories / Economic sectors / Geographic / Climate-related hazards
#   MY OWN INVENTED NAMES (not from the template, not from any standard):
#       Thematic/Ecosystem   (the dropdown has "Thematic targets", but the mined content
#                             is ecosystem typology, so I coined a different name — decision needed)
#       Instruments/Other    (my catch-all for plans/policies/knowledge-systems concepts)
#       Finance/MOI dimensions (PASS 2; my name for the finance cluster the dropdown lacks)
# Assignment mechanism: hand-curated membership sets (eyeball, criteria = "which axis of
# disaggregation does this value belong to"), then keyword fallback, else UNASSIGNED.
# ----------------------------------------------------------------------------
def guess_cat(c):
    soc = {"sex", "sex/gender", "age", "disability", "income", "indigenous peoples",
           "migrants", "refugees", "children", "youth", "women", "older persons", "household"}
    eco = {"crops", "livestock", "fisheries", "aquaculture", "agroforestry", "forestry",
           "agriculture subsector", "food type", "sector", "industry", "manufacturing",
           "energy", "transport", "tourism", "water supply", "sanitation"}
    geo = {"national", "subnational", "local", "regional", "global", "urban", "rural",
           "basin", "transboundary", "city", "province"}
    haz = {"flood", "drought", "tropical cyclone", "storm surge", "sea level rise",
           "heatwave", "wildfire", "landslide", "glacial lake outburst"}
    eco_sys = {"terrestrial", "inland waters", "marine", "coastal", "mountain", "wetlands",
               "lakes", "rivers", "aquifers", "forest", "mangroves", "coral reefs", "ecosystem"}
    if c in soc: return "Social categories"
    if c in eco: return "Economic sectors"
    if c in geo: return "Geographic"
    if c in haz: return "Climate-related hazards"
    if c in eco_sys: return "Thematic/Ecosystem"
    for kw, cat in (("ecosystem", "Thematic/Ecosystem"), ("hazard", "Climate-related hazards"),
                    ("sector", "Economic sectors"), ("plan", "Instruments/Other"),
                    ("policy", "Instruments/Other"), ("level", "Geographic"),
                    ("infrastructure", "Instruments/Other")):
        if kw in c: return cat
    return "UNASSIGNED"


# ----------------------------------------------------------------------------
# STEP 3 / PASS 2 — second-pass sets for the 61 tokens PASS 1 left UNASSIGNED
# (hand-curated after inspecting the UNASSIGNED list; same eyeball criteria)
# ----------------------------------------------------------------------------
FIN = {"insurance", "multilateral", "bilateral", "concessional loan", "non-concessional loan",
       "grant", "guarantee", "equity", "financial instrument", "financial instruments",
       "channel", "provided", "received", "mobilised", "domestic", "international",
       "international private finance", "direct access entities"}
ECO_SYS2 = {"biome", "realm", "ecological zones", "nature-based solutions",
            "effective area-based conservation measures"}
GEO_HYDRO = {"water", "type of water bodies", "additional river basins",
             "including transboundary basins", "transboundary risks", "geographical area"}
SOC2 = {"communities", "local communities", "poor",
        "split if overshoot measures address vulnerable groups"}
ECON2 = {"formal", "informal", "formality"}
INSTR = {"thematic targets", "thematic target", "ews components in target 10a", "goals",
         "strategy", "instrument", "technology", "capacity building components",
         "adaptation technology development", "timeframe", "party", "international lists",
         "internationally listed", "intangible cultural heritage elements",
         "indigenous building practices", "guided by traditional", "traditional territories",
         "participatory development process"}
DROP = {"if applicable", "the ci", "equivalent", "includes information individual basin",
        "cross-cutting considerations as appropriate", "other", "geography: local"}

PASS2 = [(FIN, "Finance/MOI dimensions"), (ECO_SYS2, "Thematic/Ecosystem"),
         (GEO_HYDRO, "Geographic"), (SOC2, "Social categories"),
         (ECON2, "Economic sectors"), (INSTR, "Instruments/Other"), (DROP, "DROP")]


# ----------------------------------------------------------------------------
# Run the pipeline and print the audit summary
# ----------------------------------------------------------------------------
concept = defaultdict(lambda: {"freq": 0, "inds": set(), "raw": set()})
for _, r in raw.iterrows():
    for t in toks(str(r.iloc[3])):
        n = norm_map.get(t, t)          # STEP 2 applied mechanically
        if n is None:
            continue
        concept[n]["freq"] += 1
        concept[n]["inds"].add(r.iloc[0])
        if t != n:
            concept[n]["raw"].add(t)    # provenance: which raw variants were merged

main = {k: v for k, v in concept.items() if v["freq"] >= 2 or len(v["inds"]) >= 2}
print("indicators:", len(raw), "| unique normalized concepts:", len(concept),
      "| main candidates (freq>=2):", len(main))

assign = {}
for k in main:
    c = guess_cat(k)                    # PASS 1
    if c == "UNASSIGNED":               # PASS 2
        for s, cat in PASS2:
            if k in s:
                c = cat
                break
    assign[k] = c
print(Counter(assign.values()))
for k in sorted(main, key=lambda x: -main[x]["freq"])[:15]:
    print(f"  {main[k]['freq']:2d}x  {assign[k]:24s}  {k}   (merged: {sorted(main[k]['raw']) or '-'})")
