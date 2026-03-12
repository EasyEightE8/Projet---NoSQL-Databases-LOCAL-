from core.database import DatabaseManager

class MilanoRepository:
    def __init__(self):
        
        # Initialize database connections
        self.db = DatabaseManager()
        self.mongo = self.db.get_mongo_db()
    
    def create_user(self, user_data):
        
        # Save user document in MongoDB
        self.mongo.users.insert_one(user_data) 
        
        # Create user node in Neo4j graph
        with self.db.get_neo4j_session() as session:
            session.run(
                "MERGE (u:User {user_id: $uid, username: $uname})", uid=user_data["user_id"], uname=user_data["username"]
            )
            
    def update_user(self, user_id, update_data):
        
        # Update user document in MongoDB
        self.mongo.users.update_one({"user_id": user_id}, {"$set": update_data})
        
        # Update username in Neo4j if changed
        if "username" in update_data:
            with self.db.get_neo4j_session() as session:
                session.run("""
                    MATCH (u:User {user_id: $uid})
                    SET u.username = $uname
                """, uid=user_id, uname=update_data["username"])
                
    def delete_user(self, user_id):
        
        # Remove user document from MongoDB
        self.mongo.users.delete_one({"user_id": user_id})
        
        # Delete user node and all relationships in Neo4j
        with self.db.get_neo4j_session() as session:
            session.run("""
                MATCH (u:User {user_id: $uid})
                DETACH DELETE u
            """, uid=user_id)

    def create_tweet(self, tweet_data):
        
        # Save tweet document in MongoDB
        self.mongo.tweets.insert_one(tweet_data)

        # Create tweet relationships in Neo4j
        with self.db.get_neo4j_session() as session:
            
            # Create tweet node
            session.run("MERGE (t:Tweet {tweet_id: $tid})", tid=tweet_data["tweet_id"])

            # Link tweet to author
            session.run("""
                MATCH (u:User {user_id: $uid}), (t:Tweet {tweet_id: $tid})
                MERGE (u)-[:AUTHORED]->(t)
            """, uid=tweet_data["user_id"], tid=tweet_data["tweet_id"])

            # Create reply relationship if this is a reply
            if tweet_data.get("in_reply_to_tweet_id"):
                session.run("""
                    MATCH (t1:Tweet {tweet_id: $tid}), (t2:Tweet {tweet_id: $rid})
                    MERGE (t1)-[:REPLY_TO]->(t2)
                """, tid=tweet_data["tweet_id"], rid=tweet_data["in_reply_to_tweet_id"])
                
    def update_tweet(self, tweet_id, update_data):
        
        # Update tweet document in MongoDB
        self.mongo.tweets.update_one({"tweet_id": tweet_id}, {"$set": update_data})

    def delete_tweet(self, tweet_id):
        
        # Remove tweet document from MongoDB
        self.mongo.tweets.delete_one({"tweet_id": tweet_id})

        # Delete tweet node and all relationships in Neo4j
        with self.db.get_neo4j_session() as session:
            session.run("""
                MATCH (t:Tweet {tweet_id: $tid})
                DETACH DELETE t
            """, tid=tweet_id)

    def add_follow(self, follower_id, target_id):
        
        # Create follow relationship between users
        with self.db.get_neo4j_session() as session:
            session.run("""
                MATCH (a:User {user_id: $aid}), (b:User {user_id: $bid})
                MERGE (a)-[:FOLLOWS]->(b)
            """, aid=follower_id, bid=target_id)

    def get_users_followed_by_ops(self):
        
        # Get all users followed by MilanoOps
        with self.db.get_neo4j_session() as session:
            result = session.run("""
                MATCH (u:User {username: 'MilanoOps'})-[:FOLLOWS]->(target:User)
                RETURN target.username as name
            """)
            return [record["name"] for record in result]

    def get_top_tweets(self):
        
        # Get 10 most favorited tweets
        return list(self.mongo.tweets.find().sort("favorite_count", -1).limit(10))

    def get_longest_thread(self):
        
        # Find the longest reply thread
        with self.db.get_neo4j_session() as session:
            
            # Using variable length path
            result = session.run("""
                MATCH p=(start:Tweet)-[:REPLY_TO*]->(end:Tweet)
                RETURN length(p) as len, start.tweet_id as start_id
                ORDER BY len DESC LIMIT 1
            """)
            return result.single()
            
    def get_incident_tweets(self):
        
        # Get all crisis/incident tweets sorted by date
        return list(self.mongo.tweets.find({"is_incident": True}).sort("created_at", -1))