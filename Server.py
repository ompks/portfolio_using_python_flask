import os
import re
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER") or os.getenv("GMAIL_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM") or SMTP_USER
MAIL_RECIPIENT = os.getenv("MAIL_RECIPIENT", MAIL_FROM)
CONTACT_FORM_ENABLED = (
    os.getenv("CONTACT_FORM_ENABLED", "false").lower() == "true"
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@app.context_processor
def inject_config():
    return {"contact_form_enabled": CONTACT_FORM_ENABLED}


def send_contact_email(visitor_email, subject, message):
    if not SMTP_USER or not SMTP_PASSWORD:
        raise ValueError(
            "Email is not configured. Set SMTP_USER and SMTP_PASSWORD in .env"
        )

    email = EmailMessage()
    email["Subject"] = f"[Portfolio Contact] {subject}"
    email["From"] = MAIL_FROM
    email["To"] = MAIL_RECIPIENT
    email["Reply-To"] = visitor_email
    email.set_content(
        "\n".join(
            [
                "New contact form submission",
                "",
                f"From: {visitor_email}",
                f"Subject: {subject}",
                "",
                "Message:",
                message,
            ]
        )
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(email)


@app.route("/")
def my_home():
    return render_template("index.html")


@app.route("/<string:page_name>")
def html_page(page_name):
    return render_template(page_name)


@app.route("/submit_form", methods=["POST", "GET"])
def submit_form():
    if not CONTACT_FORM_ENABLED:
        flash("The contact form is temporarily unavailable.", "error")
        return redirect(url_for("html_page", page_name="contact.html"))

    if request.method != "POST":
        flash("Invalid request. Please use the contact form.", "error")
        return redirect(url_for("html_page", page_name="contact.html"))

    visitor_email = request.form.get("email", "").strip()
    subject = request.form.get("subject", "").strip()
    message = request.form.get("message", "").strip()

    if not visitor_email or not subject or not message:
        flash("Please fill in all fields.", "error")
        return redirect(url_for("html_page", page_name="contact.html"))

    if not EMAIL_PATTERN.match(visitor_email):
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("html_page", page_name="contact.html"))

    try:
        send_contact_email(visitor_email, subject, message)
    except Exception:
        flash(
            "Sorry, your message could not be sent. Please try again later.",
            "error",
        )
        return redirect(url_for("html_page", page_name="contact.html"))

    return redirect(url_for("html_page", page_name="thankyou.html"))
