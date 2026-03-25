## Ejecucion local

openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem

python -m uvicorn app.main:app --reload --port 8001

http://127.0.0.1:8001/docs

## Docker

Estructura esperada (keys al mismo nivel que app):

license-authority/
- app/
- keys/
  - private.pem
  - public.pem
- Dockerfile
- docker-compose.yml

Levantar servicio:

docker compose up --build

Endpoint:

http://127.0.0.1:8001/docs
