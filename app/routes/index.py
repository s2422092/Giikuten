# app/routes/index.py
from flask import Blueprint, render_template

index_bp = Blueprint("index", __name__)

@index_bp.route("/")
def index():
    return render_template("index/index.html")


@index_bp.route("/login")
def login():
    return render_template("index/login.html")

@index_bp.route("/registration")
def registration():
    return render_template("index/registration.html")