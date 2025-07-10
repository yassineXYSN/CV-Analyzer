from databasehr.database import engine
import databasehr.models as models

print("🛠️ Initialisation des tables...")
models.Base.metadata.create_all(bind=engine)
print("✅ Terminé.")
