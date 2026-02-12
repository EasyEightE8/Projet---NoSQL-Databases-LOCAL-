import subprocess
import time
import sys
import shutil

# --- Configuration des commandes Docker ---
MONGO_NAME = "mongo-milano"
NEO4J_NAME = "neo4j-milano"

def run_cmd(command, shell=False):
    """Exécute une commande shell et gère les erreurs."""
    try:
        # Sur Windows, shell=True est souvent nécessaire pour certaines commandes,
        # mais ici on utilise une liste d'arguments pour être plus propre.
        subprocess.check_call(command, shell=shell)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution : {e}")
        sys.exit(1)

def install():
    print("📦 Installation des dépendances...")
    run_cmd([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def start_container(name, run_command_list):
    """Tente de démarrer un conteneur, sinon le crée (équivalent du || en bash)."""
    print(f"🐳 Démarrage de {name}...")
    
    # On essaie de démarrer le conteneur existant
    result = subprocess.run(["docker", "start", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if result.returncode == 0:
        print(f"✅ {name} redémarré.")
    else:
        print(f"⚠️ {name} n'existe pas ou erreur, création en cours...")
        run_cmd(run_command_list)
        print(f"✅ {name} créé et lancé.")

def db():
    # Mongo
    start_container(MONGO_NAME, [
        "docker", "run", "-d", 
        "-p", "27017:27017", 
        "--name", MONGO_NAME, 
        "mongo:latest"
    ])
    
    # Neo4j
    start_container(NEO4J_NAME, [
        "docker", "run", "-d", 
        "-p", "7474:7474", 
        "-p", "7687:7687", 
        "--name", NEO4J_NAME, 
        "-e", "NEO4J_AUTH=none", 
        "neo4j:latest"
    ])

def stop():
    print("🛑 Arrêt des bases de données...")
    subprocess.run(["docker", "stop", MONGO_NAME, NEO4J_NAME])

def seed():
    print("🌱 Lancement du script de seed...")
    run_cmd([sys.executable, "main.py"])

def app():
    print("🚀 Lancement de l'application Streamlit...")
    # On utilise sys.executable -m streamlit pour éviter les soucis de PATH sur Windows
    run_cmd([sys.executable, "-m", "streamlit", "run", "app.py"])

def run_all():
    db()
    print("⏳ Attente de 5 secondes pour l'initialisation des DB...")
    time.sleep(5)
    install()
    seed()
    app()

def help_menu():
    print("Usage: python manage.py [commande]")
    print("Commandes disponibles :")
    print("  install - Installe les paquets Python")
    print("  db      - Démarre ou crée les conteneurs Docker")
    print("  stop    - Arrête les conteneurs")
    print("  seed    - Lance main.py")
    print("  app     - Lance Streamlit")
    print("  run     - Lance TOUT (db -> wait -> install -> seed -> app)")

# --- Point d'entrée du script ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        help_menu()
        sys.exit(1)

    command = sys.argv[1]

    if command == "install":
        install()
    elif command == "db":
        db()
    elif command == "stop":
        stop()
    elif command == "seed":
        seed()
    elif command == "app":
        app()
    elif command == "run":
        run_all()
    else:
        print(f"❌ Commande inconnue : {command}")
        help_menu()