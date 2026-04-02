#!/usr/bin/env bash
set -euo pipefail

BASE_URL="http://localhost:9900"
USERNAME="admin"
PASSWORD="admin"
LICENSE_KEY_INSTALL="Coopeuch_eyJwYXlsb2FkIjp7ImNvbXBhbnkiOiJDb29wZXVjaCIsImV4cGlyZXNfYXQiOiIyMDI2LTA1LTMxVDEzOjA3OjExWiIsImZlYXR1cmVzIjp7ImlhLWFnZW50Ijp7ImZ1bmNpb25hbGl0eSI6IkF1dG9tYXRpb24sRXhlY3V0aW9uIiwidmVyc2lvbiI6IjIwMjYuMSJ9fSwiaXNzdWVkX2F0IjoiMjAyNi0wNC0wMVQxMzowNzoxMVoiLCJpc3N1ZXIiOiJUZWNobm9sb2d5IFNvbHV0aW9ucyIsImxpY2Vuc2VfaWQiOiJjMGU1ZTY4Ny1lZTVkLTQ4YzktYjY1NC1kMmVjNDFiMTc3NGUiLCJtYWNoaW5lX2lkIjoiQ09PUDAwMSIsIm1hY2hpbmVfbG9jayI6IkNPT1AwMDEiLCJtYXhfYWN0aXZhdGlvbnMiOjUsInNpZ25hdHVyZV9hbGdvcml0aG0iOiJSU0EtU0hBMjU2Iiwic3RhdHVzIjoiYWN0aXZlIiwidHlwZSI6ImZsb2F0aW5nIiwidmVyc2lvbiI6MX0sInNpZ25hdHVyZSI6Im84RWVHNXNLQnVnZDc4SkVUdks5SnpqbDFHMU1GaWVCSDFqemFIK0pmcWQ0T2Zyc0RMYlJVOXFsbzZpU1pPZDJjRkMzOFVhZjhtQWU4T2hvZU1iazY0TXZrcGlPUCttZGNKWHM1S2NBWEFxS0Q1V1pHNFMyQlBxSGhmS0Z4YkxRL2Z2UU5CTDFzSTFYZjNwbmVQQXBoTlVUUVBlZ2lXZmM3T09HWGxBUkRqVGJWdmNVRm5tQ2x6SzZWdjhYank4cUZSeEMvNDlvQ0NMakVWNWJEMVhyMXpyWG5pZjFOemw0R3dqVWp5em91ek5PbllHeGQ4dnBYeWNic1BEd2UwMVpyMmpnbmo3Zm5hNUdCT0Q2S2ZrUG96TzZKbHlmVVNNaU85a2hjVmRieGtRejZyY3BMOHkyNDhHaVRsQ0pVK1ptNzdGY29pZy9NVlVVazJHQ2lLZ1luQT09In0"
COOKIE_JAR="${COOKIE_JAR:-cookies.txt}"
VERBOSE="${VERBOSE:-0}"

usage() {
  cat <<'EOF'
Uso:
  ./install_from_string.sh -u <usuario> -p <password> -k <license_key_install> [opciones]

Opciones:
  -u, --username    Usuario admin (o exportar USERNAME)
  -p, --password    Password (o exportar PASSWORD)
  -k, --license     license_key_install completa (o exportar LICENSE_KEY_INSTALL)
  -b, --base-url    URL base del servidor (default: http://localhost:9900)
  -c, --cookies     Ruta cookie jar (default: cookies.txt)
  -v, --verbose     Muestra más detalle (default: 0)
  -h, --help        Mostrar esta ayuda

Ejemplo:
  ./install_from_string.sh \
    -u admin \
    -p 'MiPass123' \
    -k 'PREFIX_xxxxxxxxxxxxxxxxx'
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -u|--username)
      USERNAME="${2:-}"; shift 2 ;;
    -p|--password)
      PASSWORD="${2:-}"; shift 2 ;;
    -k|--license)
      LICENSE_KEY_INSTALL="${2:-}"; shift 2 ;;
    -b|--base-url)
      BASE_URL="${2:-}"; shift 2 ;;
    -c|--cookies)
      COOKIE_JAR="${2:-}"; shift 2 ;;
    -v|--verbose)
      VERBOSE=1; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Argumento no reconocido: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$USERNAME" || -z "$PASSWORD" || -z "$LICENSE_KEY_INSTALL" ]]; then
  echo "Faltan parámetros requeridos." >&2
  usage
  exit 1
fi

rm -f "$COOKIE_JAR"

if [[ "$VERBOSE" == "1" ]]; then
  echo "[1/4] Login en $BASE_URL/login"
fi

curl -sS -L -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -X POST "$BASE_URL/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=$USERNAME" \
  --data-urlencode "password=$PASSWORD" \
  -o /dev/null

if [[ "$VERBOSE" == "1" ]]; then
  echo "[2/4] Visitando dashboard para asegurar csrf_token"
fi

curl -sS -L -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -X GET "$BASE_URL/dashboard" \
  -o /dev/null

csrf_token="$(awk '$6=="csrf_token"{print $7}' "$COOKIE_JAR" | tail -n 1)"
if [[ -z "${csrf_token:-}" ]]; then
  echo "No se pudo extraer csrf_token del cookie jar: $COOKIE_JAR" >&2
  echo "Revisa credenciales y que el servidor responda en $BASE_URL." >&2
  exit 1
fi

if [[ "$VERBOSE" == "1" ]]; then
  echo "[3/4] csrf_token obtenido correctamente"
  echo "[4/4] Instalando licencia por /api/license/install-from-string"
fi

response_headers_file="$(mktemp)"
response_body_file="$(mktemp)"

http_code="$(curl -sS -o "$response_body_file" -D "$response_headers_file" \
  -w "%{http_code}" \
  -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -X POST "$BASE_URL/api/license/install-from-string" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "license_key_install=$LICENSE_KEY_INSTALL" \
  --data-urlencode "csrf_token=$csrf_token")"

location="$(awk 'BEGIN{IGNORECASE=1} /^Location:/{sub(/\r$/,"",$2); print $2}' "$response_headers_file" | tail -n 1)"

echo "HTTP: $http_code"
if [[ -n "${location:-}" ]]; then
  echo "Location: $location"
fi

if [[ "$VERBOSE" == "1" ]]; then
  echo "Body:"
  cat "$response_body_file"
  echo
fi

if [[ "${location:-}" == "/?installed=1" ]]; then
  echo "Resultado: licencia instalada correctamente."
  rm -f "$response_headers_file" "$response_body_file"
  exit 0
fi

echo "Resultado: instalación no confirmada. Revisa Location/body para detalle." >&2
rm -f "$response_headers_file" "$response_body_file"
exit 1
