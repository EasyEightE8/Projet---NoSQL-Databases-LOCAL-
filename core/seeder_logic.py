import random
from datetime import datetime, timedelta
from faker import Faker
from core.services import SentimentService
from core.repositories import MilanoRepository

fake = Faker()
repo = MilanoRepository()
ai_service = SentimentService()

class NarrativeSeeder:
    def __init__(self):
        self.users = []
        self.tweets = [] 
        self.hashtags_common = ["milano2026", "olympics", "italy", "games"]
        self.hashtags_crisis = ["metroM1", "disaster", "transportfail", "milano2026", "shame"]

    def run(self):

        # Utilisateur Officiel
        ops_user = {
            "user_id": "u_ops", "username": "MilanoOps", 
            "role": "staff", "country": "Italy", "created_at": datetime.now()
        }
        repo.create_user(ops_user)
        self.users.append(ops_user)

        for i in range(35):
            u = {
                "user_id": f"u_{i}",
                "username": fake.user_name(),
                "role": random.choice(["fan", "volunteer", "journalist"]),
                "country": fake.country(),
                "created_at": datetime.now()
            }
            repo.create_user(u)
            self.users.append(u)

        for u in self.users:
            if u["username"] != "MilanoOps":

                if random.random() > 0.3:
                    repo.add_follow(u["user_id"], "u_ops")
                
                target = random.choice(self.users)
                if target != u:
                    repo.add_follow(u["user_id"], target["user_id"])
        
        base_time = datetime.now() - timedelta(hours=4)
        
        # Liste pour stocker les IDs des tweets créés (pour pouvoir y répondre ou retweeter)
        created_tweet_ids = []

        # --- PHASE 1 : Pre-Event Hype (80 tweets) ---
        for _ in range(80):
            u = random.choice(self.users)
            txt = f"Can't wait for the opening ceremony! {fake.sentence()}"
            # Sentiment positif (0.8)
            t_id = self._post_tweet(u, txt, self.hashtags_common, base_time, sentiment_override=0.8)
            if t_id: created_tweet_ids.append(t_id)

        # --- PHASE 2 : The Incident Metro M1 Blocked (150 tweets) ---
        for _ in range(150):
            u = random.choice(self.users)
            
            # Variable pour gérer les réponses
            reply_to_id = None
            
            # LOGIQUE DE CONVERSATION (Réponses)
            # 20% de chance de répondre à un tweet existant
            if created_tweet_ids and random.random() < 0.2:
                reply_to_id = random.choice(created_tweet_ids)
                tags = ["milano2026", "reply"]
                if u["role"] == "fan":
                    txt = f"@{u['username']} Totally agree! This is a nightmare. {fake.sentence()}"
                    sentiment_bias = -0.7
                else:
                    txt = f"@{u['username']} Hoping for a quick fix. {fake.sentence()}"
                    sentiment_bias = -0.2
            
            # LOGIQUE DE TWEET ORIGINAL (Incident)
            else:
                if u["role"] == "fan":
                    txt = f"Metro M1 is completely blocked! Smoke everywhere. Total fail! {fake.sentence()}"
                    sentiment_bias = -0.9 # Très négatif
                    tags = self.hashtags_crisis
                elif u["username"] == "MilanoOps":
                    txt = "⚠️ Alert: Technical issue on Line M1. Security teams deployed. Please remain calm."
                    sentiment_bias = -0.1
                    tags = ["milano2026", "alert", "safety"]
                else:
                    txt = f"Is anyone else stuck at Duomo? {fake.sentence()}"
                    sentiment_bias = -0.5
                    tags = self.hashtags_crisis
            
            # Création du tweet
            new_t_id = self._post_tweet(u, txt, tags, base_time + timedelta(hours=1), sentiment_override=sentiment_bias, reply_to=reply_to_id)
            if new_t_id: created_tweet_ids.append(new_t_id)

            # LOGIQUE DE RETWEET (Neo4j)
            # 10% de chance qu'un utilisateur retweet un tweet existant
            if created_tweet_ids and random.random() < 0.1:
                target_tweet = random.choice(created_tweet_ids)
                # On utilise un try/pass au cas où la méthode n'existe pas dans ton repo
                try:
                    repo.add_retweet(u["user_id"], target_tweet)
                except AttributeError:
                    # Si tu n'as pas implémenté add_retweet dans repositories.py, ça ne plantera pas
                    pass 

        self._post_tweet(ops_user, "✅ Metro M1 service restored. Sorry for the inconvenience.", ["milano2026", "update"], base_time + timedelta(hours=3), 0.5)

    def _post_tweet(self, user, text, hashtags, time_base, sentiment_override=None, reply_to=None):
        """
        Crée un tweet, l'analyse, et l'insère en base.
        Retourne l'ID du tweet créé.
        """
        # 1. Analyse IA (TextBlob)
        analysis = ai_service.analyze_tweet(text)
        
        final_score = analysis["sentiment"]
        is_incident = analysis["is_incident"]

        # 2. CORRECTION CRITIQUE : Application du sentiment forcé
        if sentiment_override is not None:
            final_score = sentiment_override
            
            # Si le sentiment forcé est très négatif, on FORCE le drapeau incident
            # C'est ça qui corrige ton bug "0 Incidents"
            if final_score < -0.3:
                is_incident = True
        
        # Creation of the tweet object
        t_id = fake.uuid4() 
        
        tweet = {
            "tweet_id": t_id,
            "user_id": user["user_id"],
            "text": text,
            "hashtags": hashtags,
            "created_at": time_base + timedelta(minutes=random.randint(1, 59)),
            "favorite_count": random.randint(0, 500),
            "in_reply_to_tweet_id": reply_to, 
            "is_incident": is_incident,
            "sentiment_score": final_score
        }
        
        repo.create_tweet(tweet)
        
        return t_id