import sys
from core.database import DatabaseManager
from core.seeder_logic import NarrativeSeeder

def reset_database():    
    db = DatabaseManager()
    
    # Vidange MongoDB
    try:
        db.mongo_db.users.drop()
        db.mongo_db.tweets.drop()
        print("   -> MongoDB: Collections 'users' et 'tweets' supprimées.")
    except Exception as e:
        print(f"   -> Erreur Mongo: {e}")

    # Vidange Neo4j
    try:
        with db.get_neo4j_session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("   -> Neo4j: Tous les nœuds et relations supprimés.")
    except Exception as e:
        print(f"   -> Erreur Neo4j: {e}")

def print_stats():
    db = DatabaseManager()
    
    nb_users = db.mongo_db.users.count_documents({})
    nb_tweets = db.mongo_db.tweets.count_documents({})
    nb_incidents = db.mongo_db.tweets.count_documents({"is_incident": True})

def main():
    
    reset_database()

    try:
        seeder = NarrativeSeeder()
        seeder.run()
    except Exception as e:
        print(f"Erreur critique pendant le seeding : {e}")
        sys.exit(1)
        
    print_stats()

    DatabaseManager().close()

if __name__ == "__main__":
    main()