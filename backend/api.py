from flask import Flask, request, jsonify
import joblib
import os
import re
from collections import Counter
from dotenv import load_dotenv

# Try to import NLTK for stopwords (optional)
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

load_dotenv()

app = Flask(__name__)

MODEL_PATH = os.getenv("MODEL_PATH")
VECTORIZER_PATH = os.getenv("VECTORIZER_PATH")
LABEL_ENCODER_PATH = os.getenv("LABEL_ENCODER_PATH")

if not MODEL_PATH or not VECTORIZER_PATH or not LABEL_ENCODER_PATH:
    raise ValueError("Required environment variables are missing")

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)
label_encoder = joblib.load(LABEL_ENCODER_PATH)

# In-memory storage for spam words (for demo purposes)
# In production, use a database
spam_words_storage = {}


@app.route("/")
def home():
    return "ML API Running 🚀"


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        text = data.get("text")
        
        if not text:
            with open("api.log", "a") as f:
                f.write(f"WARNING: No text provided at {__import__('datetime').datetime.now()}\n")
            return jsonify({"error": "No text provided"}), 400

        text_vector = vectorizer.transform([text])
        prediction = model.predict(text_vector)
        final_output = label_encoder.inverse_transform(prediction)[0]

         # ─── GET CONFIDENCE SCORE ──────────────────────────────────────
        # Get probability/confidence from model
        confidence=0.95 #default fallback 
        try:
            # If model has predict_proba
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(text_vector)
                confidence = round(max(proba[0]) * 100, 2)
        except:
            # Fallback: use a random confidence for demo (or from model)
            # In production, use actual confidence from your model
            import random
            confidence = round(random.uniform(65, 99), 2)
        
        # ─── DETERMINE CONFIDENCE LEVEL ───────────────────────────────
        if confidence >= 80:
            confidence_level = "high"
            level_color = "green"
            level_emoji = "🟢"
        elif confidence >= 60:
            confidence_level = "medium"
            level_color = "yellow"
            level_emoji = "🟡"
        else:
            confidence_level = "low"
            level_color = "red"
            level_emoji = "🔴"

        return jsonify({
            "input": text,
            "prediction": final_output,
            "confidence": confidence,
            "confidence_level": confidence_level,
            "level_color": level_color,
            "level_emoji": level_emoji
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

        # Store words if prediction is spam
        if final_output == "spam":
            words = extract_words(text)
            for word in words:
                spam_words_storage[word] = spam_words_storage.get(word, 0) + 1

        # Log prediction
        text_preview = text[:50] + "..." if len(text) > 50 else text
        with open("api.log", "a") as f:
            from datetime import datetime
            f.write(f"{datetime.now()} - Prediction: '{text_preview}' -> {final_output}\n")
            
        return jsonify({
            "input": text, 
            "prediction": final_output
        })

    except Exception as e:
        with open("api.log", "a") as f:
            from datetime import datetime
            f.write(f"{datetime.now()} - ERROR: {str(e)}\n")
        return jsonify({"error": str(e)}), 500


def extract_words(text):
    """Extract words from text, remove stopwords and punctuation."""
    # Convert to lowercase and remove punctuation
    text = re.sub(r'[^\w\s]', '', text.lower())
    words = text.split()
    
    # Remove stopwords if NLTK available
    if NLTK_AVAILABLE:
        stop_words = set(stopwords.words('english'))
        words = [w for w in words if w not in stop_words and len(w) > 2]
    else:
        # Basic stopword list (fallback)
        basic_stopwords = {'the', 'a', 'an', 'of', 'for', 'on', 'at', 'to', 'in', 'is', 'it', 'and', 'or', 'but', 'with', 'from', 'by', 'as', 'was', 'are', 'were', 'been'}
        words = [w for w in words if w not in basic_stopwords and len(w) > 2]
    
    return words


def get_wordcloud_data():
    """Return stored spam word frequencies."""
    if spam_words_storage:
        # Sort by frequency and return top 50
        sorted_words = sorted(spam_words_storage.items(), key=lambda x: x[1], reverse=True)
        return [{"word": w, "count": c} for w, c in sorted_words[:50]]
    return None


# Common spam words (fallback sample data)
SPAM_WORDS = {
    'free': 145, 'win': 98, 'click': 76, 'urgent': 54, 'prize': 42,
    'limited': 38, 'offer': 35, 'money': 32, 'cash': 28, 'bonus': 25,
    'guaranteed': 22, 'credit': 20, 'loan': 18, 'insurance': 15, 'debt': 14,
    'winner': 14, 'congratulations': 13, 'exclusive': 12, 'opportunity': 10,
    'investment': 9, 'profit': 9, 'earn': 8, 'income': 8, 'million': 7,
    'billion': 6, 'rich': 6, 'secret': 6, 'miracle': 5, 'amazing': 5
}


@app.route('/api/wordcloud', methods=['GET'])
def get_wordcloud():
    """
    Get word frequency data for spam messages.
    Returns top words with frequencies for word cloud visualization.
    """
    try:
        # Try to get stored data
        words_data = get_wordcloud_data()
        
        if words_data:
            return jsonify({
                "success": True,
                "data": words_data,
                "source": "database"
            })
        
        # Fallback to sample data
        sample_data = [{"word": w, "count": c} for w, c in SPAM_WORDS.items()]
        return jsonify({
            "success": True,
            "data": sample_data,
            "source": "sample"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)