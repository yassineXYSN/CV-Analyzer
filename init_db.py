from database import engine
import databaseclient.models as models

print("🛠️ Initialisation des tables...")
models.Base.metadata.create_all(bind=engine)
print("✅ Terminé.")