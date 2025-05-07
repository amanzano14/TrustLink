from flask import Flask, render_template, request, redirect, url_for
import re
import sqlite3

app = Flask(__name__)

# Base de datos
def init_db():
    with sqlite3.connect("data.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS enlaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                riesgo TEXT NOT NULL,
                motivo TEXT
            )
        """)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analizar', methods=['POST'])
def analizar():
    url = request.form['url']
    riesgo = 'Seguro'
    motivo = 'Sin problemas detectados'

    if "@" in url or url.count("http") > 1 or re.search(r"[0-9]{5,}", url):
        riesgo = 'Peligroso'
        motivo = 'Enlace sospechoso: contiene @, múltiples http o cadenas numéricas largas.'
    elif any(keyword in url for keyword in ['free', 'win', 'login', 'bank']):
        riesgo = 'Sospechoso'
        motivo = 'Palabras clave sospechosas detectadas.'

    with sqlite3.connect("data.db") as conn:
        conn.execute("INSERT INTO enlaces (url, riesgo, motivo) VALUES (?, ?, ?)", (url, riesgo, motivo))

    return render_template('resultado.html', url=url, riesgo=riesgo, motivo=motivo)

@app.route('/reportar', methods=['GET', 'POST'])
def reportar():
    if request.method == 'POST':
        url = request.form['url']
        motivo = request.form['motivo']
        with sqlite3.connect("data.db") as conn:
            conn.execute("INSERT INTO enlaces (url, riesgo, motivo) VALUES (?, ?, ?)", (url, 'Reportado', motivo))
        return redirect(url_for('consultar'))
    return render_template('reportar.html')

@app.route('/consultar')
def consultar():
    with sqlite3.connect("data.db") as conn:
        cursor = conn.execute("SELECT url, riesgo, motivo FROM enlaces ORDER BY id DESC")
        enlaces = cursor.fetchall()
    return render_template('consultar.html', enlaces=enlaces)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8080)