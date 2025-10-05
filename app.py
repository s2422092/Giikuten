# app.py
from app import create_app   # ← app/__init__.py の create_app をインポート

app = create_app()

if __name__ == '__main__':
    print("アクセスURL: http://localhost:5055")
    app.run(debug=True, port=5055)
