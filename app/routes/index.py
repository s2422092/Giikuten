# app/routes/index.py
from flask import Blueprint, render_template

index_bp = Blueprint("index", __name__)

@index_bp.route("/")
def index():
    return render_template("index.html")


@index_bp.route("/login")
def login():
    return render_template("login.html")

@index_bp.route("/registartion")
def registartion():
    return render_template("registaration.html")