import requests
from bs4 import BeautifulSoup

BASE_URL = "http://14.139.221.18:9001/default.aspx?ReturnUrl=%2f"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "http://14.139.221.18:9001",
    "Referer": BASE_URL,
}

def get_form_fields(html):
    soup = BeautifulSoup(html, "html.parser")
    fields = {}
    for i in soup.find_all("input", {"name": True}):
        fields[i["name"]] = i.get("value", "")
    return fields, soup

session = requests.Session()
session.headers.update(HEADERS)

# Step 1: GET login page
resp1 = session.get(BASE_URL)
form1, _ = get_form_fields(resp1.text)

# Step 2: POST to trigger "Forgot Password"
form2 = form1.copy()
form2["__EVENTTARGET"] = "lnkForgot"
resp2 = session.post(BASE_URL, data=form2)

form_forgot, soup2 = get_form_fields(resp2.text)

# Debug: check if txtPassReset exists
if "txtPassReset" not in form_forgot:
    print("❌ Still not reaching Forgot Password page.")
    print("🔎 Status:", resp2.status_code)
    print("🔎 First 400 chars of resp2:\n", resp2.text[:400])
    exit()

# Step 3: Submit reset
username = input("Enter username for password reset: ").strip()
form_forgot["txtPassReset"] = username
form_forgot["btnReset"] = "Send Link to Reset Password"

resp3 = session.post(BASE_URL, data=form_forgot)

print("🔎 Status:", resp3.status_code)
print("🔎 Final URL:", resp3.url)
print("🔎 First 500 chars of response:\n", resp3.text[:500])
