
import db_manager
import sqlite3

db_manager.init_db()
conn = sqlite3.connect("predictions.db")
c = conn.cursor()
c.execute("DELETE FROM model_configs WHERE api_key = 'your_key_here'")
conn.commit()
conn.close()
print("Removed invalid models.", flush=True)
