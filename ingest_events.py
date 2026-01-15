import psycopg2
from datetime import datetime
import random

conn = psycopg2.connect("dbname=safetypulse user=postgres password=postgres")
cur = conn.cursor()

for _ in range(50):
    cur.execute(
        """INSERT INTO raw_events (device_id, event_type, severity, event_time)
           VALUES (%s, %s, %s, %s)""" ,
        (
            f"device_{random.randint(1,5)}",
            random.choice(["FALL", "OVERHEAT", "COLLISION"]),
            random.randint(1,5),
            datetime.utcnow()
        )
    )

conn.commit()
cur.close()
conn.close()