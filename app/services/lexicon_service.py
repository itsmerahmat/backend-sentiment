"""
Lexicon-based Sentiment Analysis Service

Service untuk melakukan analisis sentimen menggunakan metode lexicon/kamus kata.
Berdasarkan notebook SENTIMENT ANALYST.ipynb
"""

import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from functools import lru_cache

from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

from app.core.config import settings


# ============================================================
# Lexicon Dictionary Loading from CSV
# ============================================================


def _get_kata_value(row: Dict[str, Any]) -> str:
    """Extract 'Kata' value from row, handling BOM and different key names."""
    # Try different possible key names (with/without BOM)
    for key in row.keys():
        if key.strip().lower().replace('\ufeff', '') == 'kata':
            return row[key]
    return row.get('Kata', row.get('\ufeffKata', ''))


def _get_bobot_value(row: Dict[str, Any]) -> str:
    """Extract 'Bobot' value from row."""
    return row.get('Bobot', row.get('bobot', '0'))


@lru_cache(maxsize=1)
def load_kamus_positif() -> Dict[str, float]:
    """Load kamus positif dari CSV file."""
    kamus = {}
    csv_path = Path(settings.LEXICON_DIR) / "kamus_positif.csv"
    
    if not csv_path.exists():
        print(f"Warning: {csv_path} not found, using empty dict")
        return kamus
    
    # Use utf-8-sig to handle BOM automatically
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            kata = _get_kata_value(row).strip().lower()
            bobot_str = _get_bobot_value(row).strip()
            if kata and bobot_str:
                try:
                    # Positif CSV has positive weights
                    bobot = float(bobot_str)
                    kamus[kata] = abs(bobot)  # Ensure positive
                except ValueError:
                    continue
    
    print(f"Loaded {len(kamus)} positive words from CSV")
    return kamus


@lru_cache(maxsize=1)
def load_kamus_negatif() -> Dict[str, float]:
    """Load kamus negatif dari CSV file."""
    kamus = {}
    csv_path = Path(settings.LEXICON_DIR) / "kamus_negatif.csv"
    
    if not csv_path.exists():
        print(f"Warning: {csv_path} not found, using empty dict")
        return kamus
    
    # Use utf-8-sig to handle BOM automatically
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            kata = _get_kata_value(row).strip().lower()
            bobot_str = _get_bobot_value(row).strip()
            if kata and bobot_str:
                try:
                    # Negatif CSV has negative weights
                    bobot = float(bobot_str)
                    kamus[kata] = -abs(bobot)  # Ensure negative
                except ValueError:
                    continue
    
    print(f"Loaded {len(kamus)} negative words from CSV")
    return kamus


def get_kamus_positif() -> Dict[str, float]:
    """Get kamus positif (cached)."""
    return load_kamus_positif()


def get_kamus_negatif() -> Dict[str, float]:
    """Get kamus negatif (cached)."""
    return load_kamus_negatif()


def get_kamus_sentimen() -> Dict[str, float]:
    """Get combined sentiment lexicon."""
    return {**get_kamus_positif(), **get_kamus_negatif()}

# Kata-kata negasi
KATA_NEGASI: Set[str] = {
    "tidak", "bukan", "kurang", "salah", "belum",
    "ga", "gak", "ngga", "nggak", "gk",
    "kd", "kdd", "kda", "kada", "kadada",
    "hilang", "non", "no", "gagal",
    "jangan", "anti", "tanpa"
}

# Normalisasi slang
NORMALISASI_DICT: Dict[str, str] = {
    "kada": "tidak",
    "kadada": "tidak",
    "ga": "tidak",
    "gk": "tidak",
    "gak": "tidak",
    "ngga": "tidak",
    "nggak": "tidak",
    "kdd": "tidak",
    "kd": "tidak",
}


# ============================================================
# Preprocessing Functions
# ============================================================

# Emoji pattern
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002500-\U00002BEF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "\U0001F018-\U0001F270"
    "\U0001F000-\U0001F02F"
    "]+",
    flags=re.UNICODE
)


@lru_cache(maxsize=1)
def get_stopwords() -> Set[str]:
    """Get stopwords set (cached)."""
    stop_factory = StopWordRemoverFactory()
    stopwords_default = set(stop_factory.get_stop_words())
    
    # Stopword manual
    stopwords_manual = {"ya","yg", "deh", "dong", "nih", "sih", "aja", "jawab", "lah", "te","nya","ny", "kalasenja", "ig","wadahjajaan", "kreator"}
    
    stopwords = stopwords_default.union(stopwords_manual)
    
    # Pertahankan kata tertentu
    stopwords = stopwords.difference({"ada", "bisa", "boleh", "raum", "anu","lain", "selain",})
    stopwords = stopwords.difference(KATA_NEGASI)
    
    return stopwords


@lru_cache(maxsize=1)
def get_stemmer():
    """Get Sastrawi stemmer (cached)."""
    stem_factory = StemmerFactory()
    return stem_factory.create_stemmer()


def normalize_word(word: str) -> str:
    """Normalize slang words."""
    return NORMALISASI_DICT.get(word, word)


def clean_text(text: str) -> str:
    """Clean text by removing URLs, mentions, emojis, and special characters."""
    if not text:
        return ""
    
    text = text.lower()
    
    # Hapus URL & mention
    text = re.sub(r"http\S+|www\S+|@\S+", " ", text)
    # Simpan isi hashtag (#enak -> enak)
    text = re.sub(r"#(\w+)", r"\1", text)
    # Hapus emoji
    text = EMOJI_PATTERN.sub(" ", text)
    # Sisakan huruf dan spasi
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def preprocess_text(text: str, use_stemming: bool = True) -> List[str]:
    """
    Full preprocessing pipeline.
    
    Args:
        text: Input text
        use_stemming: Whether to apply stemming
        
    Returns:
        List of preprocessed tokens
    """
    text = clean_text(text)
    tokens = text.split()
    
    # Normalize
    tokens = [normalize_word(w) for w in tokens]
    
    # Remove stopwords
    stopwords = get_stopwords()
    tokens = [w for w in tokens if w not in stopwords]
    
    # Stemming (optional)
    if use_stemming:
        stemmer = get_stemmer()
        tokens = [stemmer.stem(w) for w in tokens]
    
    return tokens


# ============================================================
# Sentiment Scoring
# ============================================================

def hitung_sentimen_tokens(
    tokens: List[str],
    base_negator_weight: float = -1.0,
    lookahead: int = 3
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate sentiment score with negation handling.
    
    Args:
        tokens: List of preprocessed tokens
        base_negator_weight: Default weight for standalone negator
        lookahead: How many tokens ahead to look for negation target
        
    Returns:
        Tuple of (total_score, matched_words_dict)
    """
    # Load kamus dari CSV (cached)
    kamus_positif = get_kamus_positif()
    kamus_negatif = get_kamus_negatif()
    
    total = 0.0
    matched_words: Dict[str, float] = {}
    i = 0
    n = len(tokens)
    
    while i < n:
        w = tokens[i].strip().lower()
        
        if w in KATA_NEGASI:
            flipped = False
            # Cari target berkamus di 1..lookahead token berikutnya
            for j in range(i + 1, min(i + 1 + lookahead, n)):
                nxt = tokens[j].strip().lower()
                if nxt in kamus_positif:
                    score = -kamus_positif[nxt]
                    total += score
                    matched_words[f"tidak {nxt}"] = score
                    i = j + 1
                    flipped = True
                    break
                elif nxt in kamus_negatif:
                    score = -kamus_negatif[nxt]
                    total += score
                    matched_words[f"tidak {nxt}"] = score
                    i = j + 1
                    flipped = True
                    break
            
            if not flipped:
                # Negator berdiri sendiri tanpa target berkamus
                score = kamus_negatif.get(w, base_negator_weight)
                total += score
                matched_words[w] = score
                i += 1
            continue
        
        # Kata biasa
        if w in kamus_positif:
            score = kamus_positif[w]
            total += score
            matched_words[w] = score
        elif w in kamus_negatif:
            score = kamus_negatif[w]
            total += score
            matched_words[w] = score
        
        i += 1
    
    return total, matched_words


def klasifikasi_sentimen(skor: float) -> str:
    """Classify sentiment based on score."""
    if skor > 0:
        return "Positif"
    elif skor < 0:
        return "Negatif"
    else:
        return "Netral"


# ============================================================
# Public API
# ============================================================

def predict_sentiment_lexicon(texts: List[str], use_stemming: bool = True) -> List[Dict[str, Any]]:
    """
    Predict sentiment for multiple texts using lexicon method.
    
    Args:
        texts: List of input texts
        use_stemming: Whether to apply stemming
        
    Returns:
        List of prediction dicts
    """
    results = []
    
    for text in texts:
        tokens = preprocess_text(text, use_stemming=use_stemming)
        score, matched_words = hitung_sentimen_tokens(tokens)
        label = klasifikasi_sentimen(score)
        
        results.append({
            "label": label,
            "score": score,
            "tokens": tokens,
            "matched_words": matched_words
        })
    
    return results


def predict_sentiment_lexicon_single(text: str, use_stemming: bool = True) -> Dict[str, Any]:
    """Predict sentiment for a single text."""
    results = predict_sentiment_lexicon([text], use_stemming=use_stemming)
    return results[0]
