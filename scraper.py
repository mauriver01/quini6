import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import psycopg2
from database import get_conn

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def scrape_ultimo_sorteo():
    """
    Intenta obtener el último sorteo del Quini 6 desde quini-6-resultados.com.ar
    Retorna dict con fecha y números, o None si falla.
    """
    url = "https://www.quini-6-resultados.com.ar/quini6/sorteos-anteriores.aspx"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        log_scraper("error", f"No se pudo conectar al sitio: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # Buscar tabla de sorteos
    rows = soup.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 7:
            texts = [c.get_text(strip=True) for c in cells]
            # Buscar fila que tenga fecha y 6 números
            fecha_str = texts[0]
            try:
                # Formato esperado: DD/MM/YYYY
                fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
                nums = []
                for t in texts[1:]:
                    # Extraer número entre 00 y 45
                    if re.match(r"^\d{1,2}$", t):
                        n = int(t)
                        if 0 <= n <= 45:
                            nums.append(n)
                if len(nums) >= 6:
                    resultado = {
                        "fecha": fecha,
                        "numeros": sorted(nums[:6])
                    }
                    print(f"✅ Sorteo encontrado: {fecha} → {nums[:6]}")
                    return resultado
            except (ValueError, IndexError):
                continue

    # Fallback: intentar con quiniya.com.ar
    return scrape_fallback()


def scrape_fallback():
    """Fuente alternativa: quiniya.com.ar"""
    url = "https://quiniya.com.ar/sorteos"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Buscar números en la página
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
            hoy = date.today()
            print(f"✅ Fallback: {hoy} → {nums}")
            return {"fecha": hoy, "numeros": sorted(nums)}

    except Exception as e:
        log_scraper("error", f"Fallback también falló: {e}")

    return None


def guardar_sorteo(resultado):
    """Guarda el sorteo en PostgreSQL si no existe ya."""
    if not resultado:
        log_scraper("error", "No hay resultado para guardar.")
        return False

    fecha = resultado["fecha"]
    nums = resultado["numeros"]

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Verificar si ya existe
                cur.execute("SELECT id FROM sorteos WHERE fecha = %s", (fecha,))
                if cur.fetchone():
                    msg = f"Sorteo del {fecha} ya existe en la BD, se omite."
                    print(f"ℹ️  {msg}")
                    log_scraper("omitido", msg)
                    return False

                cur.execute("""
                    INSERT INTO sorteos (fecha, n1, n2, n3, n4, n5, n6)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (fecha, nums[0], nums[1], nums[2], nums[3], nums[4], nums[5]))
            conn.commit()

        msg = f"Sorteo {fecha} guardado: {nums}"
        print(f"💾 {msg}")
        log_scraper("ok", msg)
        return True

    except psycopg2.Error as e:
        msg = f"Error al guardar en BD: {e}"
        print(f"❌ {msg}")
        log_scraper("error", msg)
        return False


def log_scraper(status, mensaje):
    """Registra cada ejecución del scraper en la tabla de logs."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO scraper_log (status, mensaje) VALUES (%s, %s)",
                    (status, mensaje)
                )
            conn.commit()
    except Exception:
        pass  # El log no debe romper el flujo principal


def ejecutar_scraper():
    """Función principal: scrapeá y guardá."""
    print(f"🕐 Ejecutando scraper — {datetime.now()}")
    resultado = scrape_ultimo_sorteo()
    guardado = guardar_sorteo(resultado)
    return guardado
