from flask import Flask, request, render_template
import re, dns.resolver, smtplib, csv, os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def verify_email(email):
    regex = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    if not re.match(regex, email):
        return "❌ Invalid"

    domain = email.split('@')[1]

    try:
        records = dns.resolver.resolve(domain, 'MX')
        mx = str(records[0].exchange)
    except:
        return "❌ Domain Error"

    try:
        server = smtplib.SMTP(timeout=5)
        server.connect(mx)
        server.helo()
        server.mail('test@test.com')
        code, _ = server.rcpt(email)
        server.quit()

        if code == 250:
            return "✅ Valid"
        else:
            return "❌ Not Found"
    except:
        return "⚠️ Risky"

def generate_emails(name, domain):
    name = name.lower().split()
    first = name[0]
    last = name[-1] if len(name) > 1 else ""

    return [
        f"{first}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first}{last}@{domain}",
        f"{first[0]}{last}@{domain}"
    ]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/verify")
def verify():
    email = request.args.get("email")
    return verify_email(email)

@app.route("/find")
def find():
    name = request.args.get("name")
    domain = request.args.get("domain")

    emails = generate_emails(name, domain)
    results = []

    for e in emails:
        status = verify_email(e)
        results.append(f"{e} → {status}")

    return "<br>".join(results)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    results = []

    with open(path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            email = row[0]
            status = verify_email(email)
            results.append([email, status])

    result_file = os.path.join(UPLOAD_FOLDER, "result.csv")
    with open(result_file, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Email", "Status"])
        writer.writerows(results)

    return "✅ Bulk Verification Done! Check uploads/result.csv"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
