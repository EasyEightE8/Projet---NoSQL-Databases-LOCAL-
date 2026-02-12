from core.database import DatabaseManager

class MilanoRepository:
    def __init__(self):
        self.db = DatabaseManager()
        self.mongo = self.db.get_mongo_db()
    
    
    def create_user(self, user_data):
        
        # Mongo
        self.mongo.users.insert_one(user_data) 
        
        # Neo4j
        with self.db.get_neo4j_session() as session:
            session.run(
                "MERGE (u:User {user_id: $uid, username: $uname})", uid=user_data["user_id"], uname=user_data["username"]
            )

    def create_tweet(self, tweet_data):
        # Mongo
        self.mongo.tweets.insert_one(tweet_data) 
        
        # Neo4j
        with self.db.get_neo4j_session() as session:
            
            # Create Tweet Node
            session.run("MERGE (t:Tweet {tweet_id: $tid})", tid=tweet_data["tweet_id"])

            # Author Relation
            session.run("""
                MATCH (u:User {user_id: $uid}), (t:Tweet {tweet_id: $tid})
                MERGE (u)-[:AUTHORED]->(t)
            """, uid=tweet_data["user_id"], tid=tweet_data["tweet_id"])

            if tweet_data.get("in_reply_to_tweet_id"):
                session.run("""
                    MATCH (t1:Tweet {tweet_id: $tid}), (t2:Tweet {tweet_id: $rid})
                    MERGE (t1)-[:REPLY_TO]->(t2)
                """, tid=tweet_data["tweet_id"], rid=tweet_data["in_reply_to_tweet_id"])

    def add_follow(self, follower_id, target_id):
        with self.db.get_neo4j_session() as session:
            session.run("""
                MATCH (a:User {user_id: $aid}), (b:User {user_id: $bid})
                MERGE (a)-[:FOLLOWS]->(b)
            """, aid=follower_id, bid=target_id)

    def get_users_followed_by_ops(self):
        with self.db.get_neo4j_session() as session:
            result = session.run("""
                MATCH (u:User {username: 'MilanoOps'})-[:FOLLOWS]->(target:User)
                RETURN target.username as name
            """)
            return [record["name"] for record in result]

    def get_top_tweets(self):
        return list(self.mongo.tweets.find().sort("favorite_count", -1).limit(10))

    def get_longest_thread(self):
        with self.db.get_neo4j_session() as session:
            
            # Using variable length path
            result = session.run("""
                MATCH p=(start:Tweet)-[:REPLY_TO*]->(end:Tweet)
                RETURN length(p) as len, start.tweet_id as start_id
                ORDER BY len DESC LIMIT 1
            """)
            return result.single()
            
    # Crisis Mode Query
    def get_incident_tweets(self):
        return list(self.mongo.tweets.find({"is_incident": True}).sort("created_at", -1))