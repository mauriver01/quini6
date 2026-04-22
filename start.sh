#!/bin/bash
echo "🚀 Iniciando Quini 6 App..."
python3 -c "from database import init_db; init_db()"
echo "✅ BD lista. Arrancando servidor..."
exec gunicorn app:app --workers 1 --bind 0.0.0.0:$PORT --preload
