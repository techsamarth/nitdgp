import requests
from bs4 import BeautifulSoup
import getpass

# Base URL
base_url = "http://14.139.221.18:9001"
login_url = f"{base_url}/default.aspx?ReturnUrl=%2f"

# Ask user for credentials
username = input("Enter username: ")
password = getpass.getpass("Enter password: ")

# Start session
session = requests.Session()

# Step 1: GET login page
resp = session.get(login_url)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

# Step 2: Extract hidden fields
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
    "txt_username": username,
    "txt_password": password,
    "btnSubmitLogin": "Login"
}

# Step 3: POST login
login_resp = session.post(login_url, data=payload)
login_resp.raise_for_status()

# Step 4: Check success
if "Invalid Password" in login_resp.text or "Login" in login_resp.url:
    print("❌ Login failed")
else:
    # Parse response and extract name
    soup = BeautifulSoup(login_resp.text, "html.parser")

    # Your name appears inside <b style="color:#075539;"> SAMARTH<br>
    name_tag = soup.find("b", style=lambda s: s and "#075539" in s)
    if name_tag:
        name = name_tag.get_text(strip=True).split("[")[0].strip()
        print(f"✅ Login successful! Welcome {name}")
    else:
        print("✅ Login successful! (Name not found in page)")
