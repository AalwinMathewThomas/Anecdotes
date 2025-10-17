from app import create_app, db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)

with app.app_context():
    # SQL to alter the password_hash column
    db.engine.execute('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(300);')
    print("Migration applied: Increased password_hash to 300.")