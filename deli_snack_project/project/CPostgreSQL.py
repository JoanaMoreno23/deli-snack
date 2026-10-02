import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

def f_conectar():
    conexion = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        # En local (DB_HOST=localhost) normalmente no hay SSL configurado,
        # así que usamos "prefer". Cuando conectes a Aiven, pon
        # DB_SSLMODE=require en tu .env
        sslmode=os.getenv("DB_SSLMODE", "prefer")
    )
    return conexion
