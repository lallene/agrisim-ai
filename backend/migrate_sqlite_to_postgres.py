import os
import sqlite3
from datetime import datetime

from sqlalchemy import create_engine, text


SQLITE_DB = "predictions.db"
POSTGRES_URL = os.getenv("DATABASE_URL")


if not POSTGRES_URL:
    raise RuntimeError("DATABASE_URL PostgreSQL manquante.")

if not os.path.exists(SQLITE_DB):
    raise FileNotFoundError(f"Fichier SQLite introuvable : {SQLITE_DB}")


def parse_date(value):
    if not value:
        return datetime.utcnow()

    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return datetime.utcnow()


sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

pg_engine = create_engine(POSTGRES_URL)

rows = sqlite_cursor.execute("SELECT * FROM predictions").fetchall()

print(f"{len(rows)} lignes trouvées dans SQLite.")

with pg_engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            culture VARCHAR NOT NULL,
            zone VARCHAR NOT NULL,
            latitude FLOAT NOT NULL,
            longitude FLOAT NOT NULL,
            temperature FLOAT NOT NULL,
            humidite FLOAT NOT NULL,
            pluviometrie FLOAT NOT NULL,
            type_sol VARCHAR NOT NULL,
            ph FLOAT NOT NULL,
            engrais FLOAT NOT NULL,
            irrigation VARCHAR NOT NULL,
            rendement_predit FLOAT NOT NULL,
            date_prediction TIMESTAMP
        )
    """))

    for row in rows:
        conn.execute(text("""
            INSERT INTO predictions (
                culture, zone, latitude, longitude,
                temperature, humidite, pluviometrie,
                type_sol, ph, engrais, irrigation,
                rendement_predit, date_prediction
            )
            VALUES (
                :culture, :zone, :latitude, :longitude,
                :temperature, :humidite, :pluviometrie,
                :type_sol, :ph, :engrais, :irrigation,
                :rendement_predit, :date_prediction
            )
        """), {
            "culture": row["culture"],
            "zone": row["zone"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "temperature": row["temperature"],
            "humidite": row["humidite"],
            "pluviometrie": row["pluviometrie"],
            "type_sol": row["type_sol"],
            "ph": row["ph"],
            "engrais": row["engrais"],
            "irrigation": row["irrigation"],
            "rendement_predit": row["rendement_predit"],
            "date_prediction": parse_date(row["date_prediction"]),
        })

print("Migration terminée avec succès.")
sqlite_conn.close()