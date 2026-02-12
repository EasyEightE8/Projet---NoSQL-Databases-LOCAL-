from textblob import TextBlob

class SentimentService:
    def __init__(self):
        self.emergency_keywords = ["fail", "panne", "fire", "blocked", "smoke", "fight", "stuck", "closed", "emergency"]

    def analyze_tweet(self, text):
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        
        is_incident = False
        text_lower = text.lower()
        
        if sentiment < -0.3 and any(k in text_lower for k in self.emergency_keywords):
            is_incident = True
            
        return {
            "sentiment": sentiment,
            "is_incident": is_incident
        }