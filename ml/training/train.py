import os
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, accuracy_score
from sklearn.pipeline import Pipeline

def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    return text

def train_and_evaluate_target(df, target_col, models_dir):
    print("\n" + "="*50)
    print(f"Training models for target: {target_col}")
    print("="*50)
    
    # Preprocess text
    X = df["text"].apply(preprocess_text)
    y = df[target_col]
    
    # Split into train and test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Define models to compare
    candidate_models = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced'),
        "LinearSVM": LinearSVC(random_state=42, class_weight='balanced', dual=False),
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced', n_jobs=-1)
    }
    
    best_model_name = None
    best_f1 = -1.0
    best_pipeline = None
    best_report = None
    results = {}
    
    for name, clf in candidate_models.items():
        print(f"Training {name}...")
        
        # Pipeline with TF-IDF Vectorizer
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=10000)),
            ('clf', clf)
        ])
        
        # Train
        pipeline.fit(X_train, y_train)
        
        # Predict & Evaluate
        y_pred = pipeline.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='macro')
        
        results[name] = {"accuracy": acc, "f1_macro": f1}
        print(f"  Accuracy: {acc:.4f} | F1 Macro: {f1:.4f}")
        
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_pipeline = pipeline
            best_report = classification_report(y_test, y_pred)
            
    print(f"\nWinner for {target_col}: {best_model_name} with F1 Macro {best_f1:.4f}")
    print("\nClassification Report for Best Model:")
    print(best_report)
    
    # Retrain best pipeline on full dataset for maximum accuracy in production
    print(f"Retraining best architecture ({best_model_name}) on full dataset...")
    final_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=10000)),
        ('clf', candidate_models[best_model_name])
    ])
    final_pipeline.fit(X, y)
    
    # Save the pipeline (contains vectorizer and model)
    model_path = os.path.join(models_dir, f"{target_col}_pipeline.joblib")
    joblib.dump(final_pipeline, model_path)
    print(f"Saved {target_col} pipeline to {model_path}")
    
    return best_model_name, results

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ml/
    dataset_path = os.path.join(base_dir, "datasets", "synthetic_dataset.csv")
    models_dir = os.path.join(base_dir, "saved_models")
    os.makedirs(models_dir, exist_ok=True)
    
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}. Please run generate_dataset.py first.")
        return
        
    df = pd.read_csv(dataset_path)
    print(f"Loaded dataset with {len(df)} samples.")
    
    targets = ["intent", "category", "priority"]
    overall_results = {}
    
    for target in targets:
        winner, results = train_and_evaluate_target(df, target, models_dir)
        overall_results[target] = {"winner": winner, "results": results}
        
    print("\n" + "="*50)
    print("TRAINING SUMMARY")
    print("="*50)
    for target, info in overall_results.items():
        print(f"{target.upper()}:")
        print(f"  Best Model: {info['winner']}")
        for name, metrics in info['results'].items():
            print(f"    - {name}: F1 Macro = {metrics['f1_macro']:.4f}, Acc = {metrics['accuracy']:.4f}")
            
if __name__ == "__main__":
    main()
