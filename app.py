from flask import Flask
from routes import register_routes

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Đăng ký các routes từ file routes.py
register_routes(app)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
