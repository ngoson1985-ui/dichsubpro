from flask import Flask, request, jsonify, session, render_template
import sqlite3, openai

app = Flask(__name__)
app.secret_key = "sonpro123"

# ===== DATABASE =====
def db():
    return sqlite3.connect("db.sqlite3", check_same_thread=False)

def init():
    c = db().cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        email TEXT, password TEXT, plan TEXT, usage INT
    )""")
    db().commit()

init()

# ===== FRONTEND =====
@app.route("/")
def home():
    return render_template("index.html")

# ===== LOGIN =====
@app.route("/login", methods=["POST"])
def login():
    d = request.json
    c = db().cursor()

    c.execute("SELECT * FROM users WHERE email=?", (d["email"],))
    u = c.fetchone()

    if not u:
        c.execute("INSERT INTO users VALUES (?,?,?,?)",
                  (d["email"], d["password"], "free", 0))
        db().commit()

    session["user"] = d["email"]
    return {"ok": 1}

# ===== GET USER =====
def get_user():
    c = db().cursor()
    c.execute("SELECT * FROM users WHERE email=?", (session["user"],))
    return c.fetchone()

# ===== AI =====
def gpt(api_key, prompt):
    openai.api_key = api_key
    r = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return r['choices'][0]['message']['content']

def translate_pro(api_key, text):
    s1 = gpt(api_key, f"Dịch Trung → Việt giữ nguyên SRT:\n{text}")
    s2 = gpt(api_key, f"Viết lại tự nhiên, cảm xúc:\n{s1}")
    s3 = gpt(api_key, f"Sửa lỗi ngữ nghĩa:\n{s2}")
    return s3

# ===== TRANSLATE =====
@app.route("/translate", methods=["POST"])
def translate():
    data = request.json
    user = get_user()

    # FREE LIMIT
    if user[2] == "free" and user[3] >= 1:
        return {"error": "Hết lượt free, nâng cấp PRO"}

    result = translate_pro(data["api_key"], data["text"])

    c = db().cursor()
    c.execute("UPDATE users SET usage = usage + 1 WHERE email=?", (user[0],))
    db().commit()

    return {"result": result}

# ===== UPGRADE =====
@app.route("/upgrade")
def upgrade():
    c = db().cursor()
    c.execute("UPDATE users SET plan='pro' WHERE email=?", (session["user"],))
    db().commit()
    return "Đã nâng cấp PRO!"

app.run()
