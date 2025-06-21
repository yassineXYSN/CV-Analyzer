from database import engine
import models

print("🛠️ Initialisation des tables...")
models.Base.metadata.create_all(bind=engine)
print("✅ Terminé.")
