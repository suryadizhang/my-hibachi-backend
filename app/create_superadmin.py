from .database import init_user_db
from .auth import hash_password

username = input("Superadmin username: ")
password = input("Superadmin password: ")

conn = init_user_db()
c = conn.cursor()
c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
          (username, hash_password(password), "superadmin"))
conn.commit()
print("Superadmin created.")