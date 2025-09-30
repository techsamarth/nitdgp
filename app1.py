from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)

# Load CSV mapping Rollno -> ID
df = pd.read_csv("nitdgp.csv")

base_url = "http://14.139.221.18:9001"
login_url = f"{base_url}/default.aspx?ReturnUrl=%2f"

def chanakya_login(student_id, password):
    session = requests.Session()
    resp = session.get(login_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    def get_value(name):
        tag = soup.find("input", {"name": name})
        return tag["value"] if tag else ""

    payload = {
        "__LASTFOCUS": "",
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": get_value("__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": get_value("__VIEWSTATEGENERATOR"),
        "__EVENTVALIDATION": get_value("__EVENTVALIDATION"),
        "txt_username": student_id,
        "txt_password": password,
        "btnSubmitLogin": "Login"
    }

    login_resp = session.post(login_url, data=payload)
    login_resp.raise_for_status()

    if "Invalid Password" in login_resp.text or "Login" in login_resp.url:
        return None

    soup = BeautifulSoup(login_resp.text, "html.parser")
    name_block = soup.find("b", style=lambda v: v and "#075539" in v)
    return name_block.get_text(" ", strip=True) if name_block else "Unknown User"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    rollno = request.form.get("rollno")
    password = request.form.get("password")

    # Step 1: map Rollno -> ID
    row = df[df["Rollno"] == rollno]
    if row.empty:
        return "❌ Roll Number not found"

    student_id = row.iloc[0]["ID"]

    # Step 2: Try Chanakya login
    student_name = chanakya_login(student_id, password)
    if not student_name:
        return "❌ Invalid credentials"

    # Step 3: Show success page with name
    return render_template("welcome.html", name=student_name, rollno=rollno)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
