from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from auth import signup, login
import os
from datetime import datetime

# Load environment variables
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# Initialize Hugging Face Inference client
client = InferenceClient(provider="nebius", api_key=HF_TOKEN)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret")

# Ensure the image directory exists
os.makedirs("static/generated", exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def home():
    if "user" not in session:
        return redirect(url_for("login_page"))

    image_path = None
    if request.method == "POST":
        room_type = request.form.get("room_type")
        user_prompt = request.form.get("prompt")
        final_prompt = f"A {room_type.lower()} {user_prompt}"

        try:
            image = client.text_to_image(
                prompt=final_prompt,
                model="stabilityai/stable-diffusion-xl-base-1.0"
            )
            filename = f"{session['user']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            file_path = os.path.join("static", "generated", filename)
            image.save(file_path)
            image_path = file_path
        except Exception as e:
            print("❌ Image generation error:", e)
            image_path = "error"

    return render_template("index.html", username=session["user"], image=image_path)

@app.route("/signup", methods=["GET", "POST"])
def signup_page():
    error = ""
    if request.method == "POST":
        user = request.form.get("username")
        pw = request.form.get("password")
        if signup(user, pw):
            return redirect(url_for("login_page"))
        else:
            error = "⚠️ User already exists."
    return render_template("signup.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login_page():
    error = ""
    if request.method == "POST":
        user = request.form.get("username")
        pw = request.form.get("password")
        if login(user, pw):
            session["user"] = user
            return redirect(url_for("home"))
        else:
            error = "❌ Invalid credentials"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login_page"))

@app.route("/download/<filename>")
def download_image(filename):
    return send_from_directory("static/generated", filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
