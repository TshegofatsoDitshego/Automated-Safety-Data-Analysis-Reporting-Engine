import psycopg2

conn = psycopg2.connect("dbname=safetypulse user=postgres password=postgres")
cur = conn.cursor()

cur.execute("DELETE FROM processed_events")

cur.execute("""
    INSERT INTO processed_events (device_id, event_type, severity, event_time)
    SELECT device_id, event_type, severity, event_time
    FROM raw_events
    WHERE severity IS NOT NULL
""")

cur.execute("DELETE FROM safety_metrics")

cur.execute("""
    INSERT INTO safety_metrics
    SELECT device_id, COUNT(*), AVG(severity)
    FROM processed_events
    GROUP BY device_id
""")

conn.commit()
cur.close()
conn.close()