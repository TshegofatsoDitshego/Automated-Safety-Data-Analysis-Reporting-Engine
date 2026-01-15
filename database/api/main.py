from fastapi import FastAPI
import psycopg2

app = FastAPI()

def get_conn():
    return psycopg2.connect("dbname=safetypulse user=postgres password=postgres")

@app.get("/metrics")
def get_metrics():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM safety_metrics")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows