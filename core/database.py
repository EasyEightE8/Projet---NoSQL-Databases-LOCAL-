import os
from pymongo import MongoClient
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    _instance = None

    def __new__(cls):
        
        # Create instance only once
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)

            # Connect to MongoDB
            cls._instance.mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
            
            # Select database
            cls._instance.mongo_db = cls._instance.mongo_client["milano2026"]

            # Get Neo4j connection details
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            neo4j_auth = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
            
            # Connect to Neo4j
            cls._instance.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=neo4j_auth)
            
        return cls._instance

    def get_mongo_db(self):
        
        # Return MongoDB database instance
        return self.mongo_db

    def get_neo4j_session(self):
        
        # Create and return new Neo4j session
        return self.neo4j_driver.session()

    def close(self):
        
        # Close both database connections
        self.mongo_client.close()
        self.neo4j_driver.close()