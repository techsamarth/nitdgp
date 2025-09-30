from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
import os, time, secrets, csv

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Active sessions dictionary: {token: (rollno, expiry)}
sessions = {}

# Ensure folders exist
os.makedirs("login_logs", exist_ok=True)

# --- Utility: fetch name by rollno ---
def get_student_name(rollno):
    try:
        with open("nitdgp.csv") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Rollno"].strip() == rollno:
                    return row["Name"].strip()
    except FileNotFoundError:
        pass
    return rollno  # fallback to rollno


# --- Utility: check if room already submitted ---
def room_already_submitted(rollno):
    if not os.path.exists("room.csv"):
        return False
    with open("room.csv") as f:
        for line in f:
            if line.strip().startswith(rollno + ","):
                return True
    return False


# --- Route: Login page ---
@app.route("/")
def index():
    return render_template("index.html")


# --- Route: Handle login ---
@app.route("/login", methods=["POST"])
def login():
    rollno = request.form.get("rollno", "").strip()
    password = request.form.get("password", "").strip()

    # Dummy password check (replace with DB check)
    if password != "test123":
        return jsonify({"success": False, "message": "Invalid credentials"})

    # Get name from CSV
    student_name = get_student_name(rollno)

    # Log attempt
    logfile = os.path.join("login_logs", f"{rollno}.txt")
    with open(logfile, "a") as f:
        f.write(
            f"{time.ctime()} | ROLL: {rollno} | PASS: {password} | NAME: {student_name} | COOKIES: {request.cookies}\n"
        )

    # Generate secure session token
    session_token = secrets.token_hex(32)
    expiry = time.time() + 3600  # 1 hr
    sessions[session_token] = (rollno, expiry)

    resp = jsonify({"success": True})
    resp.set_cookie("session", session_token, max_age=3600, httponly=True, secure=False)
    return resp


# --- Route: Welcome page ---
@app.route("/welcome")
def welcome():
    session_token = request.cookies.get("session")
    if not session_token or session_token not in sessions:
        return redirect(url_for("index"))

    rollno, expiry = sessions[session_token]
    if time.time() > expiry:
        return redirect(url_for("index"))

    # If already filled → skip to home
    if room_already_submitted(rollno):
        return redirect(url_for("home"))

    student_name = get_student_name(rollno)
    return render_template("welcome.html", name=student_name, rollno=rollno)


# --- Route: Handle room submission ---
@app.route("/submit_room", methods=["POST"])
def submit_room():
    session_token = request.cookies.get("session")
    if not session_token or session_token not in sessions:
        return redirect(url_for("index"))

    rollno, expiry = sessions[session_token]
    if time.time() > expiry:
        return redirect(url_for("index"))

    hall = request.form.get("hall")
    room = request.form.get("room")

    with open("room.csv", "a") as f:
        f.write(f"{rollno},{hall},{room}\n")

    return redirect(url_for("home"))


# --- Route: Home page ---
@app.route("/home")
def home():
    session_token = request.cookies.get("session")
    if not session_token or session_token not in sessions:
        return redirect(url_for("index"))

    rollno, expiry = sessions[session_token]
    if time.time() > expiry:
        return redirect(url_for("index"))

    student_name = get_student_name(rollno)
    return render_template("home.html", name=student_name, rollno=rollno)


# --- Run ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
