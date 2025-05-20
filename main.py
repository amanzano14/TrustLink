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

    palabras_sospechosas = [
        # General phishing
        'free', 'win', 'giveaway', 'prize', 'bonus', 'reward', 'offer', 'promo', 'discount',
        'login', 'signin', 'verify', 'update', 'secure', 'account', 'security', 'access', 'validate',
        'urgent', 'important', 'emergency', 'alert', 'now', 'immediately', 'actfast',

        # Enlaces cortos usados en estafas
        'bit.ly', 'tinyurl', 'grabify', 'shorturl', 'rebrand.ly',

        # Fraudes comunes en Colombia
        'gob-colombia', 'colsubsidio', 'prosperidadsocial', 'ingresosolidario',
        'sena-becas', 'bono-daviplata', 'ayuda-gov', 'ayuda-solidaria',

        # Suplantación bancaria
        'bancolombia', 'daviplata', 'davivienda', 'bbogota', 'nequi', 'bancoagrario',
        'seguridad-login', 'autenticacion', 'token', 'clave', 'cajero',

        # Promociones falsas
        'exito-promociones', 'falabella-oferta', 'alkosto-regalo', 'oferta', 'bono', 'regalo',
        
        # Dominios extraños
        '.xyz', '.club', '.info', '.shop'
    ]

    # Evaluación del riesgo
    if "@" in url or url.count("http") > 1 or re.search(r"[0-9]{5,}", url):
        riesgo = 'Peligroso'
        motivo = 'Enlace sospechoso: contiene @, múltiples http o cadenas numéricas largas.'
    elif any(keyword in url.lower() for keyword in palabras_sospechosas):
        riesgo = 'Sospechoso'
        motivo = 'Palabras clave sospechosas detectadas en el enlace.'

    # Guardar en base de datos si no existe
    with sqlite3.connect("data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM enlaces WHERE url = ?", (url,))
        existente = cursor.fetchone()

        if not existente:
            cursor.execute("INSERT INTO enlaces (url, riesgo, motivo) VALUES (?, ?, ?)", (url, riesgo, motivo))

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
        cursor = conn.execute("SELECT id, url, riesgo, motivo FROM enlaces ORDER BY id DESC")
        enlaces = cursor.fetchall()
    return render_template('consultar.html', enlaces=enlaces)


@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    with sqlite3.connect("data.db") as conn:
        conn.execute("DELETE FROM enlaces WHERE id = ?", (id,))
    return redirect(url_for('consultar'))


if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5500)
