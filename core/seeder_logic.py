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
        
        # Initialize data storage and hashtag collections
        self.users = []
        self.tweets = [] 
        self.hashtags_common = ["milano2026", "olympics", "italy", "games"]
        self.hashtags_crisis = ["metroM1", "disaster", "transportfail", "milano2026", "shame"]

    def run(self):
        
        # Create official Milano operations user
        ops_user = {
            "user_id": "u_ops", "username": "MilanoOps", 
            "role": "staff", "country": "Italy", "created_at": datetime.now()
        }
        repo.create_user(ops_user)
        self.users.append(ops_user)

        # Generate 35 random users with different roles
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

        # Create follow relationships between users
        for u in self.users:
            if u["username"] != "MilanoOps":
                
                # 70% chance to follow MilanoOps
                if random.random() > 0.3:
                    repo.add_follow(u["user_id"], "u_ops")
                
                # Follow one random user
                target = random.choice(self.users)
                if target != u:
                    repo.add_follow(u["user_id"], target["user_id"])
        
        # Set timeline starting 4 hours ago
        base_time = datetime.now() - timedelta(hours=4)
        
        # Track tweet IDs for replies and retweets
        created_tweet_ids = []

        # Generate positive pre-event tweets
        for _ in range(80):
            u = random.choice(self.users)
            txt = f"Can't wait for the opening ceremony! {fake.sentence()}"
            
            # Force positive sentiment
            t_id = self._post_tweet(u, txt, self.hashtags_common, base_time, sentiment_override=0.8)
            if t_id: created_tweet_ids.append(t_id)

        # Generate crisis tweets about Metro M1 incident
        for _ in range(150):
            u = random.choice(self.users)
            
            # Initialize reply tracking
            reply_to_id = None
            
            # Create reply tweets (20% chance)
            if created_tweet_ids and random.random() < 0.2:
                reply_to_id = random.choice(created_tweet_ids)
                tags = ["milano2026", "reply"]
                if u["role"] == "fan":
                    txt = f"@{u['username']} Totally agree! This is a nightmare. {fake.sentence()}"
                    sentiment_bias = -0.7
                else:
                    txt = f"@{u['username']} Hoping for a quick fix. {fake.sentence()}"
                    sentiment_bias = -0.2
            
            # Create original incident tweets
            else:
                if u["role"] == "fan":
                    txt = f"Metro M1 is completely blocked! Smoke everywhere. Total fail! {fake.sentence()}"
                    sentiment_bias = -0.9  # Very negative
                    tags = self.hashtags_crisis
                elif u["username"] == "MilanoOps":
                    txt = "Alert: Technical issue on Line M1. Security teams deployed. Please remain calm."
                    sentiment_bias = -0.1
                    tags = ["milano2026", "alert", "safety"]
                else:
                    txt = f"Is anyone else stuck at Duomo? {fake.sentence()}"
                    sentiment_bias = -0.5
                    tags = self.hashtags_crisis
            
            # Create and store the tweet
            new_t_id = self._post_tweet(u, txt, tags, base_time + timedelta(hours=1), sentiment_override=sentiment_bias, reply_to=reply_to_id)
            if new_t_id: created_tweet_ids.append(new_t_id)

            # Add retweet relationships (10% chance)
            if created_tweet_ids and random.random() < 0.1:
                target_tweet = random.choice(created_tweet_ids)
                
                # Try to add retweet if method exists
                try:
                    repo.add_retweet(u["user_id"], target_tweet)
                except AttributeError:
                    # Skip if retweet method not implemented
                    pass 

        # Post resolution tweet from official account
        self._post_tweet(ops_user, "Metro M1 service restored. Sorry for the inconvenience.", ["milano2026", "update"], base_time + timedelta(hours=3), 0.5)

    def _post_tweet(self, user, text, hashtags, time_base, sentiment_override=None, reply_to=None):
        
        # Analyze tweet content with AI service
        analysis = ai_service.analyze_tweet(text)
        final_score = analysis["sentiment"]
        is_incident = analysis["is_incident"]

        # Apply forced sentiment if provided
        if sentiment_override is not None:
            final_score = sentiment_override
            
            # Force incident flag for very negative sentiment
            if final_score < -0.3:
                is_incident = True
        
        # Generate unique tweet ID
        t_id = fake.uuid4() 
        
        # Create tweet object with all data
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
        
        # Save tweet to database
        repo.create_tweet(tweet)
        return t_id
    
    def add_retweet(self, user_id, target_tweet_id):
        
        # Create retweet relationship in Neo4j
        with self.db.get_neo4j_session() as session:
            session.run("""
                MATCH (u:User {user_id: $uid}), (t:Tweet {tweet_id: $tid})
                MERGE (u)-[:RETWEETS]->(t)
            """, uid=user_id, tid=target_tweet_id)