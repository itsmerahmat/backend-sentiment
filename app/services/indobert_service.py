"""
IndoBERT Sentiment Analysis Service

Service untuk melakukan inferensi sentimen menggunakan model IndoBERT
yang sudah di-fine-tune dan di-export ke format ONNX.
"""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

from app.core.config import settings


# ============================================================
# Preprocessing Functions (sama dengan notebook)
# ============================================================

SLANG_DICT = {
    'ga': 'tidak',
    'gk': 'tidak',
    'nggak': 'tidak',
    'tdk': 'tidak',
    'bgt': 'banget',
    'bgtt': 'banget',
    'bangettt': 'banget',
    'dgn': 'dengan',
    'klo': 'kalau',
    'kl': 'kalau',
    'dr': 'dari',
    'sm': 'sama',
    'sbg': 'sebagai',
    'aja': 'saja',
    'kaka': 'kak',
    'kk': 'kak',
    'makasih': 'terima kasih',
    'mantul': 'mantap',
    'enakkk': 'enak',
    # Kosa kata banjar
    'kd': 'tidak',
    'kda': 'tidak',
    'kada': 'tidak',
    'jara': 'jera',
    'lawas': 'lama',
    'hangit': 'hangus',
    'knp': 'kenapa',
    'mksd': 'maksud',
    'ulun': 'saya',
    'capat': 'cepat',
    'ketuju': 'suka',
    'sgt': 'sangat',
    'pian': 'kamu',
    'rigat': 'kotor',
    'hirang': 'hitam',
    'lunuh': 'leleh',
    'larang': 'mahal',
    'kdd': 'tidak ada',
    'bulik': 'pulang',
    'hndk': 'mau',
    'handak': 'mau'
}


def remove_elongation(word: str) -> str:
    """Remove repeated characters (e.g., enakkk -> enak)."""
    return re.sub(r'(.)\1{2,}', r'\1', word)


def clean_text(text: str) -> str:
    """Clean text by removing URLs, mentions, hashtags, and special characters."""
    # Hapus URL
    text = re.sub(r'http\S+|www\S+', ' ', text)
    # Hapus mention & hashtag
    text = re.sub(r'@\w+|#\w+', ' ', text)
    # Hapus emoji/simbol (keep huruf/angka)
    text = re.sub(r'[^0-9a-zA-Z\s]', ' ', text)
    # Rapikan spasi
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def normalize_text(text: str, use_slang_normalization: bool = True) -> str:
    """Normalize text with lowercasing and slang conversion."""
    text = text.lower()
    words = text.split()
    normalized_words = []
    for w in words:
        w = remove_elongation(w)
        if use_slang_normalization:
            w = SLANG_DICT.get(w, w)
        normalized_words.append(w)
    return ' '.join(normalized_words)


def preprocess_text(text: str) -> str:
    """Full preprocessing pipeline."""
    text = clean_text(text)
    text = normalize_text(text)
    return text


# ============================================================
# Model Loading & Inference
# ============================================================

class IndoBertSentimentModel:
    """Wrapper class for IndoBERT ONNX model inference."""
    
    def __init__(self, model_dir: str):
        self.model_dir = Path(model_dir)
        self._load_config()
        self._load_tokenizer()
        self._load_onnx_session()
    
    def _load_config(self):
        """Load model config for label mapping."""
        config_path = self.model_dir / "config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        self.id2label = {int(k): v for k, v in config.get("id2label", {}).items()}
        self.label2id = config.get("label2id", {})
        self.num_labels = len(self.id2label)
    
    def _load_tokenizer(self):
        """Load tokenizer from model directory."""
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
    
    def _load_onnx_session(self):
        """Load ONNX runtime session."""
        onnx_path = self.model_dir / "model.onnx"
        
        # Use GPU if available, otherwise CPU
        providers = ['CPUExecutionProvider']
        if 'CUDAExecutionProvider' in ort.get_available_providers():
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        
        self.session = ort.InferenceSession(str(onnx_path), providers=providers)
        
        # Get input names
        self.input_names = [inp.name for inp in self.session.get_inputs()]
    
    def _softmax(self, logits: np.ndarray) -> np.ndarray:
        """Apply softmax to logits."""
        exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
        return exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
    
    def predict(self, texts: List[str], preprocess: bool = True) -> List[Dict[str, Any]]:
        """
        Predict sentiment for a list of texts.
        
        Args:
            texts: List of input texts
            preprocess: Whether to apply preprocessing
            
        Returns:
            List of prediction dicts with label, score, and all scores
        """
        if preprocess:
            texts = [preprocess_text(t) for t in texts]
        
        # Tokenize
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="np"
        )
        
        # Prepare ONNX inputs
        onnx_inputs = {}
        for name in self.input_names:
            if name == "input_ids":
                onnx_inputs[name] = encoded["input_ids"].astype(np.int64)
            elif name == "attention_mask":
                onnx_inputs[name] = encoded["attention_mask"].astype(np.int64)
            elif name == "token_type_ids" and "token_type_ids" in encoded:
                onnx_inputs[name] = encoded["token_type_ids"].astype(np.int64)
        
        # Run inference
        outputs = self.session.run(None, onnx_inputs)
        logits = outputs[0]
        
        # Convert to probabilities
        probs = self._softmax(logits)
        
        # Build results
        results = []
        for prob in probs:
            pred_idx = int(np.argmax(prob))
            pred_label = self.id2label[pred_idx]
            pred_score = float(prob[pred_idx])
            
            all_scores = {
                self.id2label[i]: float(prob[i])
                for i in range(self.num_labels)
            }
            
            results.append({
                "label": pred_label,
                "score": pred_score,
                "scores": all_scores
            })
        
        return results
    
    def predict_single(self, text: str, preprocess: bool = True) -> Dict[str, Any]:
        """Predict sentiment for a single text."""
        results = self.predict([text], preprocess=preprocess)
        return results[0]


# ============================================================
# Cached Model Instance (Singleton)
# ============================================================

_model_instance: IndoBertSentimentModel = None


def get_indobert_model() -> IndoBertSentimentModel:
    """Get or create the IndoBERT model instance (singleton)."""
    global _model_instance
    if _model_instance is None:
        model_dir = settings.INDOBERT_MODEL_DIR
        _model_instance = IndoBertSentimentModel(model_dir)
    return _model_instance


def predict_sentiment(texts: List[str]) -> List[Dict[str, Any]]:
    """Predict sentiment for multiple texts."""
    model = get_indobert_model()
    return model.predict(texts)


def predict_sentiment_single(text: str) -> Dict[str, Any]:
    """Predict sentiment for a single text."""
    model = get_indobert_model()
    return model.predict_single(text)
