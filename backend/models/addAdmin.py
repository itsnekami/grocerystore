from models import db, User  # Update this import based on your project structure
from flask import Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hellosafwaan'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
db.init_app(app)
with app.app_context():
    admin_username = 'admin'
    admin_password = 'admin'
    admin_user = User(username=admin_username, password=admin_password, is_admin=True)
    db.session.add(admin_user)
    db.session.commit()

print("Admin user created successfully.")   