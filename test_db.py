from app.database.repository import SQLiteRepository

db = SQLiteRepository()
logs = db.get_last_logs()

for log in logs:
    print(log)