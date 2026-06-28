import re
from datetime import datetime
import numpy as np
from backend.app import config

# Fallback imports setup
try:
    import dateparser
    from dateparser.search import search_dates
    HAS_DATEPARSER = True
except ImportError:
    HAS_DATEPARSER = False
    print("dateparser not installed. Date extraction will use basic regex.")

try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("sentence-transformers not installed. Semantic search will fall back to keyword matching.")

class NLPService:
    def __init__(self):
        self.model = None
        self.has_embeddings = False
        
        # Load SentenceTransformer model
        if HAS_TRANSFORMERS:
            try:
                # Use a lightweight, popular model that runs fast on CPU offline
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                self.has_embeddings = True
                print("Successfully loaded SentenceTransformer (all-MiniLM-L6-v2).")
            except Exception as e:
                print(f"Error loading SentenceTransformer: {e}. Fallback to keyword matching.")
                self.has_embeddings = False

        # Common English stop words
        self.stopwords = {
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
            "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
            "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing",
            "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
            "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
            "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is",
            "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no",
            "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves",
            "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
            "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
            "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those",
            "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
            "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while",
            "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
            "you're", "you've", "your", "yours", "yourself", "yourselves", "please", "remind", "remember", "forget",
            "want", "need", "should", "tomorrow", "today", "yesterday", "next", "week", "month", "year", "pm", "am"
        }

    # 1. Date Extraction
    def extract_due_date(self, text: str) -> str:
        """Extracts date/time from text using dateparser and returns ISO formatted string or None."""
        if not HAS_DATEPARSER:
            return self._regex_date_fallback(text)
            
        try:
            # search_dates parses sentences to find date expressions
            results = search_dates(text, languages=['en'])
            if results:
                # Grab the first match
                matched_text, dt = results[0]
                # Filter out pure numbers that could be misinterpreted as dates (e.g. "5000" in "buy 5000 items")
                # and avoid parsing times that don't indicate a clear day unless they have indicators
                if re.match(r'^\d+$', matched_text):
                    return None
                return dt.isoformat()
        except Exception as e:
            print(f"Date parsing error: {e}")
            
        return None

    def _regex_date_fallback(self, text: str) -> str:
        """Very basic regex fallback for date extraction if dateparser fails."""
        text_lower = text.lower()
        if "tomorrow" in text_lower:
            from datetime import timedelta
            return (datetime.now() + timedelta(days=1)).isoformat()
        if "today" in text_lower:
            return datetime.now().isoformat()
        return None

    # 2. Keyword & Auto-Tagging
    def extract_keywords_and_tags(self, text: str, category: str) -> list:
        """Extracts keywords and creates auto-tags combining them with the category name."""
        # Clean text
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove stopwords and unique list
        keywords = [w for w in words if w not in self.stopwords]
        
        # Build tags
        tags = set()
        tags.add(category.lower())
        
        # Add top keywords as tags (limit to 4 keywords)
        for kw in keywords[:4]:
            tags.add(kw)
            
        return list(tags)

    # 3. Vector Embeddings
    def get_embedding(self, text: str) -> list:
        """Generates semantic embedding vector. Returns empty list if disabled/fails."""
        if not self.has_embeddings:
            return []
            
        try:
            # Generate 384-dimensional vector from MiniLM
            vector = self.model.encode(text)
            return vector.tolist()
        except Exception as e:
            print(f"Embedding generation error: {e}")
            return []

    # 4. Hybrid Smart Search
    def search(self, query: str, items: list, threshold: float = 0.2) -> list:
        """Performs hybrid semantic + keyword search over item list.
        
        Each item is expected to be a dict containing 'text', 'intent', 'category', 'priority', 'status', and 'embedding'.
        Returns list of dicts with an added 'score' field, sorted by score descending.
        """
        if not items:
            return []
            
        query_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())) - self.stopwords
        
        query_vector = None
        if self.has_embeddings:
            query_vector = self.get_embedding(query)
            
        results = []
        for item in items:
            text = item.get("text", "")
            item_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())) - self.stopwords
            
            # 1. Keyword Score (Jaccard similarity)
            keyword_score = 0.0
            union = query_words.union(item_words)
            if union:
                keyword_score = len(query_words.intersection(item_words)) / len(union)
                
            # 2. Semantic Score
            semantic_score = 0.0
            item_vector = item.get("embedding", [])
            if query_vector and item_vector:
                try:
                    q_arr = np.array(query_vector)
                    i_arr = np.array(item_vector)
                    norm_q = np.linalg.norm(q_arr)
                    norm_i = np.linalg.norm(i_arr)
                    if norm_q > 0 and norm_i > 0:
                        semantic_score = float(np.dot(q_arr, i_arr) / (norm_q * norm_i))
                        # Scale cosine similarity from [-1, 1] to [0, 1]
                        semantic_score = max(0.0, (semantic_score + 1) / 2)
                except Exception as e:
                    print(f"Similarity computation error: {e}")
                    
            # 3. Hybrid Combination
            if self.has_embeddings and item_vector:
                # 80% weight on semantic, 20% on exact keywords
                score = 0.8 * semantic_score + 0.2 * keyword_score
            else:
                score = keyword_score
                
            if score >= threshold or (query.lower() in text.lower()):
                # If exact query string matches document, ensure it scores high
                if query.lower() in text.lower():
                    score = max(score, 0.5)
                
                result_item = dict(item)
                result_item["score"] = round(score, 4)
                # Remove embedding from output to save bandwidth
                if "embedding" in result_item:
                    del result_item["embedding"]
                results.append(result_item)
                
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
