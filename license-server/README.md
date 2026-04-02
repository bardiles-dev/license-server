# License Server - Despliegue para cliente

## 1) Preparar imagen en tu equipo

Desde `license-server/`:

```bash
docker build -t license-server-ts:1.0 .
docker save -o license-server-ts-1.0.tar license-server-ts:1.0
```

Archivo a entregar: `license-server-ts-1.0.tar`

## 2) Archivos a entregar al cliente

- `license-server-ts-1.0.tar`
- `docker-compose.client.yaml`
- `.env.example` (para que cree su `.env`)

## 3) Instalación en equipo cliente

1. Instalar Docker + Docker Compose.
2. Copiar archivos al servidor/PC cliente.
3. Crear `.env` a partir de `.env.example`.

Ejemplo `.env`:

```env
SECRET_KEY=CAMBIAR_ESTA_CLAVE_EN_PRODUCCION
LICENSE_SERVER_MACHINE_ID=CLIENTE-UNICO-001
```

4. Cargar imagen y levantar:

```bash
docker load -i license-server-ts-1.0.tar
docker compose -f docker-compose.client.yaml up -d
```

5. Verificar:

```bash
docker ps
docker logs license-server
```

Acceso web: `http://localhost:9900`

## 4) Actualización de versión

En tu equipo:

```bash
docker build -t license-server-ts:1.1 .
docker save -o license-server-ts-1.1.tar license-server-ts:1.1
```

En cliente:

```bash
docker load -i license-server-ts-1.0.tar
docker compose -f docker-compose.client.yaml down
docker compose -f docker-compose.client.yaml up -d
```

Si cambias solo variables de entorno (`SECRET_KEY`, `LICENSE_SERVER_MACHINE_ID`), basta editar `.env` y reiniciar:

```bash
docker compose -f docker-compose.client.yaml up -d
```