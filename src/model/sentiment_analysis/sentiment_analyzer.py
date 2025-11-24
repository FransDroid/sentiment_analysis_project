import os
import numpy as np
import pickle
import logging
from typing import Dict, List, Tuple, Optional
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from .text_preprocessor import TextPreprocessor
from config.settings import Config

try:
    import torch
    import torch.nn.functional as F
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
except ImportError:  # pragma: no cover - optional dependency
    torch = None
    F = None
    AutoModelForSequenceClassification = None
    AutoTokenizer = None

class SentimentAnalyzer:
    def __init__(self, model_dir: Optional[str] = None):
        self.preprocessor = TextPreprocessor()
        self.model = None
        self.vectorizer = None
        self.is_trained = False
        self.transformer_model = None
        self.transformer_tokenizer = None
        self.transformer_device = None
        self.transformer_label_map: Dict[int, str] = {}

        self._initialize_transformer(model_dir or Config.TRANSFORMER_MODEL_DIR)

    def textblob_sentiment(self, text: str) -> Dict:
        """Quick sentiment analysis using TextBlob"""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1

        if polarity > 0.1:
            label = 'positive'
        elif polarity < -0.1:
            label = 'negative'
        else:
            label = 'neutral'

        return {
            'label': label,
            'polarity': polarity,
            'subjectivity': subjectivity,
            'confidence': abs(polarity)
        }

    def prepare_training_data(self, texts: List[str], labels: List[str]) -> Tuple:
        """Prepare data for training"""
        processed_texts = [self.preprocessor.preprocess(text) for text in texts]

        # Convert labels to numeric
        label_map = {'negative': 0, 'neutral': 1, 'positive': 2}
        numeric_labels = [label_map[label] for label in labels]

        return processed_texts, numeric_labels

    def train_model(self, texts: List[str], labels: List[str]):
        """Train a simple sentiment analysis model"""
        try:
            processed_texts, numeric_labels = self.prepare_training_data(texts, labels)

            # Create TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
            X = self.vectorizer.fit_transform(processed_texts)

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, numeric_labels, test_size=0.2, random_state=42
            )

            # Train logistic regression model
            self.model = LogisticRegression(random_state=42)
            self.model.fit(X_train, y_train)

            # Evaluate
            accuracy = self.model.score(X_test, y_test)
            logging.info(f"Model trained with accuracy: {accuracy:.2f}")

            self.is_trained = True

        except Exception as e:
            logging.error(f"Error training model: {e}")

    def predict_sentiment(self, text: str) -> Dict:
        """Predict sentiment for a single text"""
        if not text:
            return {
                'label': 'neutral',
                'confidence': 0.0,
                'probabilities': {'negative': 0.0, 'neutral': 1.0, 'positive': 0.0}
            }

        if self.transformer_model:
            return self._predict_with_transformer(text)

        if self.is_trained and self.model and self.vectorizer:
            return self._predict_with_traditional(text)

        return self.textblob_sentiment(text)

    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze sentiment for multiple texts"""
        return [self.predict_sentiment(text) for text in texts]

    def get_sentiment_summary(self, sentiments: List[Dict]) -> Dict:
        """Calculate summary statistics for sentiments"""
        if not sentiments:
            return {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}

        counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        total = len(sentiments)

        for sentiment in sentiments:
            label = sentiment.get('label', 'neutral')
            counts[label] += 1

        return {
            'positive': counts['positive'] / total * 100,
            'neutral': counts['neutral'] / total * 100,
            'negative': counts['negative'] / total * 100,
            'total': total
        }

    def save_model(self, filepath: str):
        """Save trained model and vectorizer"""
        if self.is_trained:
            model_data = {
                'model': self.model,
                'vectorizer': self.vectorizer
            }
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)

    def load_model(self, filepath: str):
        """Load trained model and vectorizer"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            self.model = model_data['model']
            self.vectorizer = model_data['vectorizer']
            self.is_trained = True
        except Exception as e:
            logging.error(f"Error loading model: {e}")

    def _initialize_transformer(self, model_dir: Optional[str]) -> None:
        """Load transformer-based sentiment model if available."""
        if not model_dir:
            return

        if not all([AutoTokenizer, AutoModelForSequenceClassification, torch, F]):
            logging.info("Transformers dependency not available; skipping transformer model initialization")
            return

        resolved_path = os.path.abspath(model_dir)
        if not os.path.isdir(resolved_path):
            logging.info("Transformer model directory %s not found; skipping", resolved_path)
            return

        try:
            self.transformer_tokenizer = AutoTokenizer.from_pretrained(resolved_path, local_files_only=True)
            self.transformer_model = AutoModelForSequenceClassification.from_pretrained(resolved_path, local_files_only=True)
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.transformer_device = torch.device(device)
            self.transformer_model.to(self.transformer_device)
            self.transformer_model.eval()
            self.transformer_label_map = self._build_label_map()
            logging.info("Transformer sentiment model loaded from %s using %s", resolved_path, device)
        except Exception as exc:
            logging.error("Failed to load transformer model from %s: %s", resolved_path, exc)
            self.transformer_model = None
            self.transformer_tokenizer = None
            self.transformer_device = None
            self.transformer_label_map = {}

    def _build_label_map(self) -> Dict[int, str]:
        """Normalize label mappings from the transformer config."""
        if not self.transformer_model:
            return {}

        mapping: Dict[int, str] = {}
        config = self.transformer_model.config

        label2id = getattr(config, 'label2id', None)
        if isinstance(label2id, dict):
            for raw_label, raw_idx in label2id.items():
                try:
                    idx = int(raw_idx)
                except (TypeError, ValueError):
                    continue
                mapping[idx] = self._canonical_label(raw_label)

        id2label = getattr(config, 'id2label', None)
        if isinstance(id2label, dict):
            for raw_idx, raw_label in id2label.items():
                try:
                    idx = int(raw_idx)
                except (TypeError, ValueError):
                    if isinstance(raw_idx, str) and raw_idx.upper().startswith('LABEL_'):
                        try:
                            idx = int(raw_idx.split('_')[-1])
                        except ValueError:
                            continue
                    else:
                        continue
                mapping.setdefault(idx, self._canonical_label(raw_label))

        if not mapping:
            return {0: 'negative', 1: 'neutral', 2: 'positive'}

        normalized_values = set(mapping.values())
        required = {'negative', 'neutral', 'positive'}
        if required.issubset(normalized_values):
            return mapping

        sorted_indices = sorted(mapping.keys())
        fallback = {idx: label for idx, label in zip(sorted_indices, ['negative', 'neutral', 'positive'])}
        return fallback if fallback else {0: 'negative', 1: 'neutral', 2: 'positive'}

    def _canonical_label(self, label: str) -> str:
        """Map raw model labels to canonical sentiment buckets."""
        lower = (label or '').lower()
        if 'neg' in lower:
            return 'negative'
        if 'pos' in lower:
            return 'positive'
        if 'neu' in lower or 'mix' in lower:
            return 'neutral'
        if lower.startswith('label'):
            digits = ''.join(char for char in lower if char.isdigit())
            if digits:
                idx = int(digits)
                fallback = {0: 'negative', 1: 'neutral', 2: 'positive'}
                return fallback.get(idx, lower)
        return lower if lower else 'neutral'

    def _predict_with_transformer(self, text: str) -> Dict:
        """Predict sentiment using the transformer model."""
        if not all([self.transformer_model, self.transformer_tokenizer, self.transformer_device, torch, F]):
            return self.textblob_sentiment(text)

        cleaned_text = text.strip()
        if not cleaned_text:
            return {
                'label': 'neutral',
                'confidence': 0.0,
                'probabilities': {'negative': 0.0, 'neutral': 1.0, 'positive': 0.0}
            }

        try:
            inputs = self.transformer_tokenizer(
                cleaned_text,
                return_tensors='pt',
                truncation=True,
                padding=True,
                max_length=512
            )
            inputs = {key: value.to(self.transformer_device) for key, value in inputs.items()}

            with torch.no_grad():
                outputs = self.transformer_model(**inputs)
                logits = outputs.logits
                probabilities_tensor = F.softmax(logits, dim=-1)[0].detach().cpu()

            probabilities = probabilities_tensor.numpy()
            predicted_idx = int(np.argmax(probabilities))
            label = self.transformer_label_map.get(predicted_idx, 'neutral')

            return {
                'label': label,
                'confidence': float(probabilities[predicted_idx]),
                'probabilities': self._build_probability_output(probabilities)
            }
        except Exception as exc:
            logging.error(f"Error predicting sentiment with transformer model: {exc}")
            return self.textblob_sentiment(text)

    def _build_probability_output(self, probabilities: np.ndarray) -> Dict[str, float]:
        """Create a probability map keyed by canonical labels."""
        probability_map: Dict[str, float] = {}
        for idx, value in enumerate(probabilities):
            label = self.transformer_label_map.get(idx, f'label_{idx}')
            probability_map[label] = float(value)

        for label in ('negative', 'neutral', 'positive'):
            probability_map.setdefault(label, 0.0)

        return probability_map

    def _predict_with_traditional(self, text: str) -> Dict:
        """Predict sentiment using the classic TF-IDF + Logistic Regression model."""
        try:
            processed_text = self.preprocessor.preprocess(text)
            text_vector = self.vectorizer.transform([processed_text])

            prediction = self.model.predict(text_vector)[0]
            probabilities = self.model.predict_proba(text_vector)[0]

            label_map = {0: 'negative', 1: 'neutral', 2: 'positive'}
            predicted_label = label_map.get(prediction, 'neutral')

            return {
                'label': predicted_label,
                'confidence': float(np.max(probabilities)),
                'probabilities': {
                    'negative': float(probabilities[0]),
                    'neutral': float(probabilities[1]),
                    'positive': float(probabilities[2])
                }
            }
        except Exception as exc:
            logging.error(f"Error predicting sentiment with traditional model: {exc}")
            return self.textblob_sentiment(text)