# Install the required Python packages
install:
	pip install pymongo neo4j python-dotenv faker textblob pandas streamlit watchdog

# Start the databases
db:
	docker start mongo-milano || docker run -d -p 27017:27017 --name mongo-milano mongo:latest
	docker start neo4j-milano || docker run -d -p 7474:7474 -p 7687:7687 --name neo4j-milano -e NEO4J_AUTH=none neo4j:latest

# Stop the databases
stop:
	docker stop mongo-milano neo4j-milano

# Run the Python script
seed:
	python main.py

# Run the Streamlit app
app:
	streamlit run app.py

run: db
	@sleep 5
	@make seed
	@make app

# make run for running the whole project