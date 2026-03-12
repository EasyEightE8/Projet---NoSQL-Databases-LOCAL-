from textblob import TextBlob

class SentimentService:
    def __init__(self):
        
        # Define keywords that indicate emergency situations
        self.emergency_keywords = ["fail", "panne", "fire", "blocked", "smoke", "fight", "stuck", "closed", "emergency"]

    def analyze_tweet(self, text):
        
        # Calculate sentiment score using TextBlob
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        
        # Check if tweet describes an incident
        is_incident = False
        text_lower = text.lower()
        
        # Mark as incident if negative sentiment + emergency keywords
        if sentiment < -0.3 and any(k in text_lower for k in self.emergency_keywords):
            is_incident = True
            
        # Return analysis results
        return {
            "sentiment": sentiment,
            "is_incident": is_incident
        }