import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

def train_final_model():
    print("--- Training Accuracy-Optimized Model ---")
    df = pd.read_csv('fedmedflow_accurate_dataset.csv')
    
    X = df['symptoms'].astype(str).str.lower()
    y = df['name']
    
    # Analyze words, not characters, to understand medical terms
    model_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='word', ngram_range=(1, 2))),
        ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    model_pipeline.fit(X, y)
    
    with open('health_model_v2.pkl', 'wb') as f:
        pickle.dump(model_pipeline, f)
    print("✅ health_model_v2.pkl trained and saved.")

if __name__ == "__main__":
    train_final_model()