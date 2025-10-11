import tensorflow as tf
import numpy as np
import pickle
import logging
from typing import Dict, List, Tuple
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from .text_preprocessor import TextPreprocessor

class SentimentAnalyzer:
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.model = None
        self.vectorizer = None
        self.is_trained = False

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
        if not self.is_trained:
            # Fall back to TextBlob if no trained model
            return self.textblob_sentiment(text)

        try:
            processed_text = self.preprocessor.preprocess(text)
            text_vector = self.vectorizer.transform([processed_text])

            prediction = self.model.predict(text_vector)[0]
            probabilities = self.model.predict_proba(text_vector)[0]

            label_map = {0: 'negative', 1: 'neutral', 2: 'positive'}
            predicted_label = label_map[prediction]

            return {
                'label': predicted_label,
                'confidence': float(np.max(probabilities)),
                'probabilities': {
                    'negative': float(probabilities[0]),
                    'neutral': float(probabilities[1]),
                    'positive': float(probabilities[2])
                }
            }

        except Exception as e:
            logging.error(f"Error predicting sentiment: {e}")
            return self.textblob_sentiment(text)

    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze sentiment for multiple texts"""
        results = []
        for text in texts:
            sentiment = self.predict_sentiment(text)
            results.append(sentiment)
        return results

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