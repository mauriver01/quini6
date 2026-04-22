import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from database import get_conn

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def scrape_ultimo_sorteo():
    url = "https://www.quini-6-resultados.com.ar/quini6/sorteos-anteriores.aspx"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        log_scraper("error", f"No se pudo conectar al sitio: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 7:
            texts = [c.get_text(strip=True) for c in cells]
            fecha_str = texts[0]
            try:
                fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
                nums = []
                for t in texts[1:]:
                    if re.match(r"^\d{1,2}$", t):
                        n = int(t)
                        if 0 <= n <= 45:
                            nums.append(n)
                if len(nums) >= 6:
                    return {"fecha": fecha, "numeros": sorted(nums[:6])}
            except (ValueError, IndexError):
                continue

    return scrape_fallback()


def scrape_fallback():
    url = "https://quiniya.com.ar/sorteos"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        numeros_divs = soup.find_all(class_=re.compile(r"numero|ball|bolilla", re.I))
        nums = []
        for d in numeros_divs:
            t = d.get_text(strip=True)
            if re.match(r"^\d{1,2}$", t):
                n = int(t)
                if 0 <= n <= 45:
                    nums.append(n)
            if len(nums) == 6:
                break
        if len(nums) == 6:
            from datetime import date
            return {"fecha": date.today(), "numeros": sorted(nums)}
    except Exception as e:
        log_scraper("error", f"Fallback falló: {e}")
    return None


def guardar_sorteo(resultado):
    if not resultado:
        log_scraper("error", "No hay resultado para guardar.")
        return False

    fecha = resultado["fecha"]
    nums = resultado["numeros"]

    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM sorteos WHERE fecha = %s", (fecha,))
        if cur.fetchone():
            msg = f"Sorteo del {fecha} ya existe."
            log_scraper("omitido", msg)
            cur.close(); conn.close()
            return False

        cur.execute(
            "INSERT INTO sorteos (fecha, n1, n2, n3, n4, n5, n6) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (fecha, nums[0], nums[1], nums[2], nums[3], nums[4], nums[5])
        )
        conn.commit()
        cur.close(); conn.close()
        log_scraper("ok", f"Sorteo {fecha} guardado: {nums}")
        return True
    except Exception as e:
        log_scraper("error", f"Error BD: {e}")
        return False


def log_scraper(status, mensaje):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO scraper_log (status, mensaje) VALUES (%s, %s)", (status, mensaje))
        conn.commit()
        cur.close(); conn.close()
    except Exception:
        pass


def ejecutar_scraper():
    print(f"🕐 Ejecutando scraper — {datetime.now()}")
    resultado = scrape_ultimo_sorteo()
    return guardar_sorteo(resultado)
