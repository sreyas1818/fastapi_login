from database import SessionLocal
import models

db = SessionLocal()

admin = models.Admin(
    username="admin",
    password="admin123"
)

db.add(admin)
db.commit()
db.close()

print("Admin created successfully")
