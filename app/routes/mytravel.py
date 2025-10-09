from flask import Blueprint, render_template,request, redirect, url_for, flash, session
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()  # ← .envファイルの内容を読み込む

mytravel_bp = Blueprint("mytravel", __name__)

# DB接続設定を環境変数から取得
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT")
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

@mytravel_bp.route("/mytravel")
def mytravel():
    return render_template("mytravel/mytravel.html")

@mytravel_bp.route("/budget")
def budget():
    return render_template("mytravel/budget.html")

@mytravel_bp.route("/travel_history")
def travel_history():
    return render_template("mytravel/travel_history.html")

@mytravel_bp.route("/travel_timelist")
def travel_timelist():
    return render_template("mytravel/travel_timelist.html")
