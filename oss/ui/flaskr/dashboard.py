import os
import socket
from flask import (
    Blueprint, render_template, request, flash,
    redirect, url_for, send_from_directory, g
)
from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# Page d'accueil du tableau de bord
@bp.route("/")
@login_required
def index():
   db = get_db()

   commands = db.execute("SELECT timestamp, command, result FROM history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10",
        (g.user['id'],)
    ).fetchall()
   
   return render_template("dashboard/index.html", commands=commands)

# Page pour exécuter des commandes système (dans un cadre local sécurisé uniquement)
@bp.route("/execute", methods=["GET", "POST"])
@login_required
def execute():
    output = ""
    if request.method == "POST":
        command = request.form.get("command")
        if command:
            try:
                # Attention : dans un vrai environnement de production, cette méthode est dangereuse
                output = os.popen(command).read()
                flash("Commande exécutée avec succès.", "success")
            except Exception as e:
                flash(f"Erreur lors de l'exécution : {str(e)}", "danger")
        else:
            flash("Veuillez saisir une commande.", "warning")
    return render_template("dashboard/execute.html", output=output)

# Page d'upload de fichier
@bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_file():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Aucun fichier sélectionné.", "warning")
            return redirect(request.url)

        upload_path = os.path.join("uploads", file.filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)
        flash("Fichier uploadé avec succès.", "success")
        return redirect(url_for("dashboard.upload_file"))

    return render_template("dashboard/upload.html")

# Téléchargement de fichiers uploadés
@bp.route("/download/<filename>")
@login_required
def download_file(filename):
    upload_folder = os.path.abspath("uploads")
    return send_from_directory(upload_folder, filename, as_attachment=True)

# Historique des commandes ou actions utilisateurs
@bp.route("/history")
@login_required
def history():
    db = get_db()
    logs = db.execute(
        "SELECT * FROM history WHERE user_id = ? ORDER BY created DESC",
        (g.user['id'],)
    ).fetchall()
    return render_template("dashboard/history.html", logs=logs)

# Informations système et réseau (adresse IP locale, port, etc.)
@bp.route("/system")
@login_required
def system_info():
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except socket.error:
        ip = "Inconnu"

    port = 65432  # Ce port pourrait être récupéré dynamiquement d'une config
    return render_template("dashboard/system.html", ip=ip, port=port)
