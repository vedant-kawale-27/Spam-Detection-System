import joblib
import numpy as np
from lime.lime_text import LimeTextExplainer

# Load models once when the app starts (this is better for performance)
model = joblib.load('backend/linear_svm_model.pkl')
vectorizer = joblib.load('backend/tfidf_vectorizer.pkl')

def get_explanation(text):
    def predict_proba_wrapper(texts):
        features = vectorizer.transform(texts)
        decision = model.decision_function(features)
        if decision.ndim > 1:
            decision = decision[:, 1]
        probs = 1 / (1 + np.exp(-decision))
        n_samples = len(texts)
        prob_matrix = np.zeros((n_samples, 2))
        prob_matrix[:, 1] = probs
        prob_matrix[:, 0] = 1 - probs
        return prob_matrix

    explainer = LimeTextExplainer(class_names=['Ham', 'Spam'])
    exp = explainer.explain_instance(text, predict_proba_wrapper, num_features=5)
    
    # Return the data in a format ready for JSON
    return [[str(word), float(score)] for word, score in exp.as_list()]