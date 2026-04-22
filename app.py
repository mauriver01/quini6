import os
from flask import Flask, jsonify, send_from_directory, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import init_db, get_conn
from scraper import ejecutar_scraper
import pytz

app = Flask(__name__, static_folder="static")
AR_TZ = pytz.timezone("America/Argentina/Buenos_Aires")

scheduler = BackgroundScheduler(timezone=AR_TZ)
scheduler.add_job(
    ejecutar_scraper,
    CronTrigger(day_of_week="mon,thu", hour=10, minute=0, timezone=AR_TZ),
    id="scraper_quini6", replace_existing=True
)
scheduler.start()
print("⏰ Scheduler activo — lunes y jueves 10:00hs AR")

@app.route("/api/estadisticas")
def api_estadisticas():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT num, COUNT(*) as salidas FROM (
            SELECT n1 AS num FROM sorteos UNION ALL SELECT n2 FROM sorteos
            UNION ALL SELECT n3 FROM sorteos UNION ALL SELECT n4 FROM sorteos
            UNION ALL SELECT n5 FROM sorteos UNION ALL SELECT n6 FROM sorteos
        ) t GROUP BY num ORDER BY num
    """)
    rows = cur.fetchall()
    freq = {i: 0 for i in range(46)}
    for row in rows:
        freq[row[0]] = row[1]

    cur.execute("SELECT COUNT(*) FROM sorteos")
    total = cur.fetchone()[0]

    cur.execute("SELECT fecha, n1, n2, n3, n4, n5, n6 FROM sorteos ORDER BY fecha DESC LIMIT 1")
    ultimo = cur.fetchone()
    cur.close(); conn.close()

    return jsonify({
        "total_sorteos": total,
        "ultimo_sorteo": {
            "fecha": str(ultimo[0]) if ultimo else None,
            "numeros": list(ultimo[1:]) if ultimo else []
        },
        "frecuencias": [{"n": n, "salidas": freq[n]} for n in range(46)]
    })

@app.route("/api/patrones")
def api_patrones():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT n1,n2,n3,n4,n5,n6 FROM sorteos")
    sorteos = cur.fetchall()
    cur.close(); conn.close()

    if not sorteos:
        return jsonify({})

    total = len(sorteos)
    pares = impares = 0
    rangos = [0,0,0,0,0]
    c0 = c1 = c2 = 0
    sumas = []

    for s in sorteos:
        nums = sorted(s)
        sumas.append(sum(nums))
        for n in nums:
            if n % 2 == 0: pares += 1
            else: impares += 1
            if n <= 9: rangos[0] += 1
            elif n <= 19: rangos[1] += 1
            elif n <= 29: rangos[2] += 1
            elif n <= 39: rangos[3] += 1
            else: rangos[4] += 1
        consec = sum(1 for i in range(len(nums)-1) if nums[i+1]-nums[i]==1)
        if consec == 0: c0 += 1
        elif consec == 1: c1 += 1
        else: c2 += 1

    tn = total * 6
    return jsonify({
        "pares_pct": round(pares/tn*100, 1),
        "impares_pct": round(impares/tn*100, 1),
        "rangos": [round(r/tn*100, 1) for r in rangos],
        "consecutivos": {
            "cero": round(c0/total*100, 1),
            "uno": round(c1/total*100, 1),
            "dos_plus": round(c2/total*100, 1)
        },
        "suma_media": round(sum(sumas)/len(sumas), 1)
    })

@app.route("/api/logs")
def api_logs():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT ejecutado, status, mensaje FROM scraper_log ORDER BY ejecutado DESC LIMIT 20")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([{"ejecutado": str(r[0]), "status": r[1], "mensaje": r[2]} for r in rows])

@app.route("/api/scraper/forzar")
def forzar_scraper():
    secret = os.environ.get("ADMIN_SECRET", "")
    if not secret or request.args.get("secret") != secret:
        return jsonify({"error": "No autorizado"}), 403
    result = ejecutar_scraper()
    return jsonify({"guardado": result})

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
