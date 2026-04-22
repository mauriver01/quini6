import os
from flask import Flask, jsonify, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import init_db, get_conn
from scraper import ejecutar_scraper
import pytz

app = Flask(__name__, static_folder="static")
AR_TZ = pytz.timezone("America/Argentina/Buenos_Aires")

# ─── SCHEDULER ────────────────────────────────────────────────────────────────

scheduler = BackgroundScheduler(timezone=AR_TZ)

# Jueves y lunes a las 10:00hs Argentina
scheduler.add_job(
    ejecutar_scraper,
    CronTrigger(day_of_week="mon,thu", hour=10, minute=0, timezone=AR_TZ),
    id="scraper_quini6",
    replace_existing=True
)
scheduler.start()
print("⏰ Scheduler activo — corre lunes y jueves a las 10:00hs AR")

# ─── API ENDPOINTS ─────────────────────────────────────────────────────────────

@app.route("/api/estadisticas")
def api_estadisticas():
    """
    Retorna frecuencias históricas de todos los números (00–45)
    calculadas desde la BD.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT num, COUNT(*) as salidas
                FROM (
                    SELECT n1 AS num FROM sorteos
                    UNION ALL SELECT n2 FROM sorteos
                    UNION ALL SELECT n3 FROM sorteos
                    UNION ALL SELECT n4 FROM sorteos
                    UNION ALL SELECT n5 FROM sorteos
                    UNION ALL SELECT n6 FROM sorteos
                ) t
                GROUP BY num
                ORDER BY num
            """)
            rows = cur.fetchall()

            # Asegurar que los 46 números estén presentes aunque tengan 0 salidas
            freq = {i: 0 for i in range(46)}
            for num, count in rows:
                freq[num] = count

            cur.execute("SELECT COUNT(*) FROM sorteos")
            total_sorteos = cur.fetchone()[0]

            cur.execute("""
                SELECT fecha, n1, n2, n3, n4, n5, n6
                FROM sorteos
                ORDER BY fecha DESC
                LIMIT 1
            """)
            ultimo = cur.fetchone()

    return jsonify({
        "total_sorteos": total_sorteos,
        "ultimo_sorteo": {
            "fecha": str(ultimo[0]) if ultimo else None,
            "numeros": list(ultimo[1:]) if ultimo else []
        },
        "frecuencias": [
            {"n": n, "salidas": freq[n]} for n in range(46)
        ]
    })


@app.route("/api/sorteos")
def api_sorteos():
    """Retorna los últimos 100 sorteos."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT fecha, n1, n2, n3, n4, n5, n6
                FROM sorteos
                ORDER BY fecha DESC
                LIMIT 100
            """)
            rows = cur.fetchall()

    return jsonify([
        {
            "fecha": str(r[0]),
            "numeros": list(r[1:])
        } for r in rows
    ])


@app.route("/api/patrones")
def api_patrones():
    """Calcula patrones: pares/impares, rangos, consecutivos."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT n1,n2,n3,n4,n5,n6 FROM sorteos")
            sorteos = cur.fetchall()

    if not sorteos:
        return jsonify({})

    total = len(sorteos)
    pares = impares = 0
    rangos = [0, 0, 0, 0, 0]  # 0-9, 10-19, 20-29, 30-39, 40-45
    consecutivos_0 = consecutivos_1 = consecutivos_2plus = 0
    sumas = []

    for s in sorteos:
        nums = sorted(s)
        suma = sum(nums)
        sumas.append(suma)

        for n in nums:
            if n % 2 == 0:
                pares += 1
            else:
                impares += 1
            if n <= 9:    rangos[0] += 1
            elif n <= 19: rangos[1] += 1
            elif n <= 29: rangos[2] += 1
            elif n <= 39: rangos[3] += 1
            else:         rangos[4] += 1

        # Contar pares consecutivos
        consec = sum(1 for i in range(len(nums)-1) if nums[i+1] - nums[i] == 1)
        if consec == 0:   consecutivos_0 += 1
        elif consec == 1: consecutivos_1 += 1
        else:             consecutivos_2plus += 1

    total_nums = total * 6
    suma_media = sum(sumas) / len(sumas)

    return jsonify({
        "pares_pct": round(pares / total_nums * 100, 1),
        "impares_pct": round(impares / total_nums * 100, 1),
        "rangos": [round(r / total_nums * 100, 1) for r in rangos],
        "consecutivos": {
            "cero": round(consecutivos_0 / total * 100, 1),
            "uno": round(consecutivos_1 / total * 100, 1),
            "dos_plus": round(consecutivos_2plus / total * 100, 1)
        },
        "suma_media": round(suma_media, 1)
    })


@app.route("/api/scraper/forzar")
def forzar_scraper():
    """Endpoint para forzar el scraper manualmente (útil para testing)."""
    secret = os.environ.get("ADMIN_SECRET", "")
    if request.args.get("secret") != secret or not secret:
        return jsonify({"error": "No autorizado"}), 403
    result = ejecutar_scraper()
    return jsonify({"guardado": result})


@app.route("/api/logs")
def api_logs():
    """Últimos 20 logs del scraper."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ejecutado, status, mensaje
                FROM scraper_log
                ORDER BY ejecutado DESC
                LIMIT 20
            """)
            rows = cur.fetchall()
    return jsonify([
        {"ejecutado": str(r[0]), "status": r[1], "mensaje": r[2]}
        for r in rows
    ])


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ─── INIT ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
