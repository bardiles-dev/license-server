Comando para lanzar (desarrollo):
```bash
python -m uvicorn app.main:app --reload --port 9000
```

Entorno local:
```bash
python -m venv venv
pip install -r requirements.txt
```

Docker (producción):
```bash
cp .env.example .env   # editar SECRET_KEY
# Debe existir public.pem en la raíz del proyecto (clave pública de license-authority)
docker build -t license-server .
docker compose up -d
```
Acceso: http://localhost:9000
docker build -t license-server .