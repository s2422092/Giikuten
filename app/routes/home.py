from flask import Blueprint, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import session   


home_bp = Blueprint("home", __name__)

## DB接続
DB_CONFIG = {
    "host": "localhost",
    "dbname": "kazino",
    "user": "yugo_suzuki",
    "password": "your_password",  # 環境に合わせて修正
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)


@home_bp.route("/home")
def home():
    return render_template("home.html")
