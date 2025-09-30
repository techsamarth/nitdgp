import requests
from bs4 import BeautifulSoup
import getpass

# Base URL
base_url = "http://14.139.221.18:9001"
login_url = f"{base_url}/default.aspx?ReturnUrl=%2f"

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

username = input("Enter username: ")
password = getpass.getpass("Enter password: ")

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
    soup = BeautifulSoup(login_resp.text, "html.parser")
    # Extract welcome name
    name_block = soup.find("b", style=lambda v: v and "#075539" in v)
    role_block = soup.find("b", style=lambda v: v and "#139867" in v)

    if name_block:
        name = name_block.get_text(strip=True)
        role = role_block.get_text(" ", strip=True) if role_block else ""
        print(f"✅ Login successful\nWelcome {name} {role}")
    else:
        print("✅ Login successful (could not parse name)")

    # 🔎 Print session cookies
    print("\n🍪 Session Cookies:")
    for cookie in session.cookies:
        print(f"  {cookie.name} = {cookie.value}")
