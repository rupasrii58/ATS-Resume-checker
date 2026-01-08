import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
import PyPDF2

# ================= CONFIG =================
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

client = genai.Client(api_key="AIzaSyCtExDJ6RbY3ilhA-SM02_6gaPBjAUkcRg")

app = Flask(__name__)
CORS(app)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ================= PDF TEXT =================
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

# ================= ANALYZE ROUTE =================

from flask import render_template

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return jsonify({"error": "Resume required"}), 400

    resume_file = request.files["resume"]
    job_description = request.form.get("job_description")

    if not job_description:
        return jsonify({"error": "Job description required"}), 400

    pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_file.filename)
    resume_file.save(pdf_path)

    resume_text = extract_text_from_pdf(pdf_path)

    prompt = f"""
You are an ATS system.

Compare Resume and Job Description.

Return ONLY valid JSON in this format:
{{
  "score": 0-100,
  "matchAnalysis": {{
    "skillsMatch": 0-100,
    "experienceMatch": 0-100,
    "formatting": 0-100
  }},
  "missingKeywords": [],
  "strengths": [],
  "improvementTips": [],
  "verdict": ""
}}

Resume:
{resume_text}

Job Description:
{job_description}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    match = re.search(r"\{.*\}", response.text, re.S)
    if not match:
        return jsonify({"error": "Invalid AI response"}), 500

    return jsonify(eval(match.group()))

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True, port=8080)