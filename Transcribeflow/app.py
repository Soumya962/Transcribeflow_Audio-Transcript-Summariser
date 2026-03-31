from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from whisper_utils import transcribe_audio
from summarisation import summarize_text
import mysql.connector
import os
import base64
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ---------------- DATABASE ----------------
db = mysql.connector.connect(
    host="localhost",
    user="sihi",
    password="1728",
    database="transcribeflow"
)
cursor = db.cursor()

# ---------------- UPLOAD FOLDER ----------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ---------------- HOME ----------------
@app.route('/')
def index():
    return render_template("login.html")


# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():

    username = request.form['username']
    password = request.form['password']

    query = "SELECT * FROM users WHERE username=%s AND password=%s"
    cursor.execute(query, (username, password))
    result = cursor.fetchone()

    if result:
        session['username'] = username
        return redirect(url_for('upload_page'))

    return "Invalid credentials"


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        query = "INSERT INTO users (username,password) VALUES (%s,%s)"
        cursor.execute(query,(username,password))
        db.commit()

        return redirect(url_for('index'))

    return render_template("register.html")


# ---------------- UPLOAD + TRANSCRIBE ----------------
@app.route('/upload', methods=['GET','POST'])
def upload_page():

    if 'username' not in session:
        return redirect(url_for('index'))

    transcription = None
    summary = None
    txt_filename = None
    json_filename = None
    uploaded_filename = None

    if request.method == "POST":

        file = request.files.get("file")

        if file and file.filename != "":

            uploaded_filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_filename)

            file.save(file_path)

            # Transcription
            transcription = transcribe_audio(file_path)

            # Summary
            summary = summarize_text(transcription)

            base = uploaded_filename.rsplit(".",1)[0]

            txt_filename = base + ".txt"
            json_filename = base + ".json"

            # Save TXT
            with open(os.path.join(UPLOAD_FOLDER,txt_filename),"w",encoding="utf-8") as f:
                f.write(transcription)

            # Save JSON
            with open(os.path.join(UPLOAD_FOLDER,json_filename),"w") as f:
                json.dump({
                    "transcription": transcription,
                    "summary": summary
                },f)

    return render_template(
        "upload.html",
        transcription=transcription,
        summary=summary,
        txt_filename=txt_filename,
        json_filename=json_filename,
        uploaded_filename=uploaded_filename
    )


# ---------------- LIVE RECORD ----------------
@app.route('/record', methods=['POST'])
def record_audio():

    data = request.json['audio']
    audio_data = base64.b64decode(data.split(',')[1])

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    audio_filename = f"recorded_{timestamp}.wav"
    file_path = os.path.join(UPLOAD_FOLDER,audio_filename)

    with open(file_path,"wb") as f:
        f.write(audio_data)

    transcription = transcribe_audio(file_path)
    summary = summarize_text(transcription)

    txt_filename = f"live_{timestamp}.txt"
    json_filename = f"live_{timestamp}.json"

    # Save TXT
    with open(os.path.join(UPLOAD_FOLDER,txt_filename),"w",encoding="utf-8") as f:
        f.write(transcription)

    # Save JSON
    with open(os.path.join(UPLOAD_FOLDER,json_filename),"w") as f:
        json.dump({
            "transcription":transcription,
            "summary":summary
        },f)

    return jsonify({
        "transcription": transcription,
        "summary": summary,
        "txt_file": txt_filename,
        "json_file": json_filename,
        "audio_file": audio_filename
    })


# ---------------- DOWNLOAD ----------------
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('username',None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
