import re
from typing import List, Set

# Common chemical solvents, reagents, and abbreviations in research literature
COMMON_SOLVENTS_AND_REAGENTS = {
    "DCM", "THF", "ETME", "ETOBAC", "ETOAC", "MEOH", "ETOH", "ACOH", "CDCL3",
    "DMSO", "DMF", "MECN", "ET2O", "TFA", "HEXANES", "PENTANE", "TOLUENE",
    "ACETONE", "PYRIDINE", "TEA", "DIEA", "DIPEA", "DMAP", "EDC", "HOBT",
    "HATU", "NABH4", "LIAlH4", "NAOH", "KOH", "K2CO3", "CS2CO3", "NAHCO3",
    "PD(PPH3)4", "PD(DPPF)CL2", "PDC", "PCC", "NBS", "NCS", "TMS", "TBS",
    "TBDMS", "BOC", "FMOC", "CBP", "BINAP"
}

# Chemical formula regex matching Stoichiometric formulas like H2O, C8H10N4O2, Fe2O3, CH3COOH, Pd(PPh3)4, PtCl2(dppf)
CHEM_FORMULA_PATTERN = re.compile(
    r"\b(?:[A-Z][a-z]?\d*){2,}\b|\b[A-Z][a-z]?\d*\(?:[A-Z][a-z]?\d*\)+\d*\b"
)

# SMILES string candidate heuristics (minimum 5 chars, containing valid SMILES tokens)
SMILES_PATTERN = re.compile(
    r"\b(?=[A-Za-z0-9#=\-\+\(\)\[\]\\\/]{5,})(?:C|N|O|S|P|F|Cl|Br|I|c|n|o|s)+(?:[=#\-\+\(\)\[\]\\\/0-9]+[A-Za-z0-9#=\-\+\(\)\[\]\\\/]*)*\b"
)

# Common IUPAC / Organic chemistry suffixes
IUPAC_SUFFIX_PATTERN = re.compile(
    r"\b[a-zA-Z]{3,}(?:one|ol|ate|ic acid|amide|amine|azole|benzene|thiophene|pyridine|furan|pyrrole|indole|quinoline|ester|ether|aldehyde|ketone|alkyne|alkene)\b",
    re.IGNORECASE
)

# Standard English words to filter out if caught by formula/SMILES regex
STOP_WORDS = {
    "AND", "FOR", "THE", "WAS", "NOT", "BUT", "ALL", "ARE", "HAS", "OUT",
    "CAN", "ITS", "NEW", "TWO", "MAY", "OUR", "SEE", "WAY", "WHO", "BOY",
    "DAY", "DID", "GET", "HIM", "MAN", "OLD", "TOO", "USE", "FIG", "TAB",
    "PAGE", "REF", "VOL", "EQ", "EX", "PAG", "PDF", "SEC"
}

def extract_chemical_entities(text: str) -> List[str]:
    """
    Extracts chemical entity candidates (formulas, solvents, SMILES, IUPAC terms)
    from text.
    """
    if not text:
        return []

    entities: Set[str] = set()

    # 1. Match known solvents & reagents
    words = re.findall(r"\b[A-Za-z0-9_\-\(\)]+\b", text)
    for w in words:
        w_upper = w.upper()
        if w_upper in COMMON_SOLVENTS_AND_REAGENTS:
            entities.add(w)

    # 2. Match chemical formulas (e.g. C8H10N4O2, H2SO4, Fe2O3, CH3COOH)
    formulas = CHEM_FORMULA_PATTERN.findall(text)
    for f in formulas:
        if f.upper() not in STOP_WORDS and len(f) >= 2:
            # Require at least one digit or parenthesis or lower-case element pair to avoid plain English words
            if any(char.isdigit() for char in f) or "(" in f or re.search(r"[A-Z][a-z]", f):
                entities.add(f)

    # 3. Match potential SMILES strings
    smiles_candidates = SMILES_PATTERN.findall(text)
    for s in smiles_candidates:
        if s.upper() not in STOP_WORDS and len(s) >= 5:
            # Check for characteristic SMILES characters (=, #, @, ring numbers, parentheses)
            if any(c in s for c in ["=", "#", "@", "(", ")", "1", "2", "3"]):
                entities.add(s)

    # 4. Match IUPAC terms
    iupac_terms = IUPAC_SUFFIX_PATTERN.findall(text)
    for term in iupac_terms:
        if len(term) >= 4 and term.upper() not in STOP_WORDS:
            entities.add(term)

    return sorted(list(entities))
