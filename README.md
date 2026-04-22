# 🎯 Quini 6 — Analizador Estadístico

App web con scraping automático, base de datos PostgreSQL y análisis de patrones.  
Se actualiza sola cada **lunes y jueves a las 10:00hs (Argentina)**.

---

## 📁 Estructura del proyecto

```
quini6/
├── app.py              ← Servidor Flask + scheduler automático
├── scraper.py          ← Scraper del sitio de resultados
├── database.py         ← Conexión y creación de tablas PostgreSQL
├── requirements.txt    ← Dependencias Python
├── Procfile            ← Comando de inicio para Railway
├── start.sh            ← Script de arranque alternativo
└── static/
    └── index.html      ← Frontend completo
```

---

## 🚀 Cómo deployar en Railway (paso a paso)

### Paso 1 — Crear cuenta en GitHub
Si no tenés, creá una en https://github.com  
Es gratis.

### Paso 2 — Subir el código a GitHub
1. Entrá a https://github.com/new
2. Nombre del repo: `quini6-analizador`
3. Hacelo **privado** (recomendado)
4. Hacé click en "Create repository"
5. En tu PC, abrí una terminal en la carpeta `quini6/` y ejecutá:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/quini6-analizador.git
git push -u origin main
```

### Paso 3 — Crear cuenta en Railway
1. Entrá a https://railway.app
2. Registrate con tu cuenta de GitHub (más fácil)

### Paso 4 — Crear el proyecto en Railway
1. En el dashboard de Railway, hacé click en **"New Project"**
2. Elegí **"Deploy from GitHub repo"**
3. Seleccioná `quini6-analizador`
4. Railway detecta automáticamente que es Python

### Paso 5 — Agregar PostgreSQL
1. En tu proyecto de Railway, hacé click en **"New"** → **"Database"** → **"PostgreSQL"**
2. Railway crea la base de datos y genera automáticamente la variable `DATABASE_URL`
3. ¡No necesitás hacer nada más, se conecta solo!

### Paso 6 — Configurar variables de entorno
En Railway, andá a tu servicio → **"Variables"** → agregá:
```
ADMIN_SECRET=una_clave_secreta_que_elijas
```
(Esta clave te permite forzar el scraper manualmente si querés)

### Paso 7 — Deployar
Railway deployea automáticamente al conectar el repo.  
En 2-3 minutos tu app está disponible en una URL tipo:  
`https://quini6-analizador-production.up.railway.app`

---

## ✅ Verificar que funciona

1. Abrí la URL de tu app
2. Debería cargar con los datos históricos (si ya hay sorteos en la BD)
3. Andá a la pestaña **"Logs"** para ver el estado del scraper

---

## 🕐 Horario del scraper automático

| Día | Hora (Argentina) | Sorteo que busca |
|-----|-----------------|-----------------|
| Jueves | 10:00hs | Sorteo del miércoles |
| Lunes | 10:00hs | Sorteo del domingo |

---

## 🔧 Forzar el scraper manualmente

Si querés actualizar sin esperar al horario automático:
```
https://tu-app.railway.app/api/scraper/forzar?secret=tu_clave_secreta
```

---

## 📱 Acceso desde cualquier dispositivo

Una vez deployado, la misma URL funciona desde:
- ✅ PC
- ✅ Celular  
- ✅ Tablet
- ✅ Cualquier navegador

---

## 💰 Costo en Railway

El plan gratuito incluye **$5 USD de crédito mensual**.  
Esta app consume aproximadamente **$0.50–1 USD/mes**.  
Básicamente gratis.
