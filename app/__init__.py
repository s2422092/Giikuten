# app/__init__.py
from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv()  # .env を使う場合（任意）

def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    # 🔑 セッション用の秘密鍵を設定
    # .env に SECRET_KEY があればそちらを使う。なければデフォルト文字列を使う
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_dev_secret_key")

    # Blueprint の登録
    from .routes.index import index_bp
    from .routes.home import home_bp


    app.register_blueprint(index_bp)
    app.register_blueprint(home_bp)

    return app
