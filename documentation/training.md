# Model Training Guide

The SysAi productivity engine operates entirely offline using locally trained classifiers. This guide details how the dataset is generated and how classification models are compared and trained.

---

## 📊 1. Synthetic Dataset Generator

The training data is generated programmatically by `ml/datasets/generate_dataset.py` using natural templates filled with random entities.
- **Dataset Size**: at least 5,500 unique labeled texts.
- **Targets**:
  1. **Intent**: `Task`, `Note`, `Reminder`, `Todo`
  2. **Category**: `Study`, `Work`, `Shopping`, `Health`, `Personal`, `Finance`
  3. **Priority**: `Low`, `Medium`, `High`

To enrich target distributions, 15% of the entries are programmatically injected with natural language date markers (e.g. *"tomorrow"*, *"this weekend"*, *"June 30th"*), and 10% are injected with urgent modifiers (e.g. *"ASAP"*, *"low priority though"*) to teach models priority indicators.

---

## ⚙️ 2. Machine Learning Pipelines

Each target is trained using an independent scikit-learn pipeline composed of:
1. **Preprocessor**: Lowercases and strips whitespaces.
2. **Feature Extractor**: `TfidfVectorizer` configured with `ngram_range=(1, 2)` (unigrams and bigrams) and `max_features=10000` to learn task-specific patterns and words.
3. **Classifiers**: The script trains and compares three architectures:
   - **Logistic Regression**: with balanced class weights.
   - **Linear SVM (LinearSVC)**: with balanced class weights.
   - **Random Forest**: 100 trees, parallel execution.

---

## 🏆 3. Evaluation and Selection

The training script performs an 80/20 train-test split stratified on the target class. It evaluates each model on the test set using Macro-F1 Score and Accuracy:
- **Comparison Log**:
  - The script prints classification reports for all three candidate models.
  - The model architecture with the highest **Macro-F1 Score** is chosen as the winner.
- **Winner Retraining**:
  - The chosen winner architecture is automatically retrained on the **100% full dataset** to maximize classification precision in production.
  - The entire final pipeline (vectorizer + model) is exported to `ml/saved_models/` as a single joblib file:
    - `intent_pipeline.joblib`
    - `category_pipeline.joblib`
    - `priority_pipeline.joblib`

---

## ⚡ Running the Training Script

To re-run dataset generation and models comparison, execute:
```bash
# 1. Generate new data
python ml/datasets/generate_dataset.py

# 2. Re-train models
python ml/training/train.py
```
Upon script completion, you will see a `TRAINING SUMMARY` in the terminal detailing the winner for each target (e.g. *Winner for intent: RandomForest with F1 Macro 0.9851*). The backend automatically reloads these files on its next inference query.
