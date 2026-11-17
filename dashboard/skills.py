"""The ten skills: codes, order, names in Portflow and categories (docs/vaardigheden-openict.md)."""

import unicodedata

SKILLS = ["OC", "KO", "JKO", "KPM", "PL", "BD", "SW", "FO", "PH", "RE"]
PRODUCT_SKILLS = ["OC", "KO", "JKO", "KPM"]
COACH_SKILLS = ["PL", "BD", "SW", "FO", "PH", "RE"]

NAMES = {
    "OC": "Overzicht creëren",
    "KO": "Kritisch oordelen",
    "JKO": "Juiste kennis ontwikkelen",
    "KPM": "Kwalitatief product maken",
    "PL": "Plannen",
    "BD": "Boodschap delen",
    "SW": "Samenwerken",
    "FO": "Flexibel opstellen",
    "PH": "Pro-actief handelen",
    "RE": "Reflecteren",
}

# Category per skill, for the column header colours (docs/design-system.md, categories from LEF).
CATEGORY = {code: "product" for code in PRODUCT_SKILLS}
CATEGORY.update({code: "social" for code in ["PL", "BD", "SW"]})
CATEGORY.update({code: "personal" for code in ["FO", "PH", "RE"]})

def goal_name_key(name: str | None) -> str:
    """Spec 005, F14: a comparison key for a Portflow goal name. Portflow spells the skills in
    several ways ("Kritisch Oordelen", "Overzicht Creëeren", "Proactief Handelen", "ë" as NFD),
    so ignore capitals, Unicode form, accents, hyphens and spaces, and doubled letters."""
    text = unicodedata.normalize("NFD", unicodedata.normalize("NFC", name or "").casefold())
    letters = [c for c in text if c.isalnum()]   # drops the combining accents, hyphens and spaces
    return "".join(c for i, c in enumerate(letters) if i == 0 or c != letters[i - 1])


_BY_NAME = {goal_name_key(name): code for code, name in NAMES.items()}
assert len(_BY_NAME) == len(NAMES)   # the keys of the ten skills stay distinct


def skill_for_goal_name(name: str | None) -> str | None:
    """Portflow goal name -> skill code, or None for any other goal (spec 005, F14)."""
    return _BY_NAME.get(goal_name_key(name))
