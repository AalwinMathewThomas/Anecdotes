from app import create_app, db
from app.schema import User  # Adjust if your User model is in schema.py

app = create_app()

with app.app_context():
    # Alter the password_hash column to VARCHAR(300)
    db.engine.execute("ALTER TABLE \"user\" ALTER COLUMN password_hash TYPE VARCHAR(300);")
    print("Migration applied: Increased password_hash to 300.")