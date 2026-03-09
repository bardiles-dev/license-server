# CI / GitHub Actions

Workflow: **`.github/workflows/ci.yml`**

## Jobs

| Job | Descripción |
|-----|-------------|
| **Lint** | Ruff sobre `license-server/app` y `license-authority/app`. |
| **Dependency audit (pip-audit)** | Vulnerabilidades en dependencias Python (PyPI). Ejecuta `pip-audit` por proyecto. |
| **OWASP Dependency-Check** | Análisis CVE/NVD con imagen oficial Docker. Genera SARIF y se sube a la pestaña Security. |
| **SonarCloud** | Análisis de calidad y seguridad. Requiere `SONAR_TOKEN` en GitHub Secrets. |
| **SAST (Bandit)** | Análisis estático de seguridad sobre el código Python. |
| **DAST (OWASP ZAP)** | Escaneo baseline contra license-server (solo en push a `main`). La app se levanta en el job. |

## Secrets necesarios

- **`SONAR_TOKEN`**: para SonarCloud. Crear proyecto en [sonarcloud.io](https://sonarcloud.io), vincular el repo y copiar el token a **Settings → Secrets and variables → Actions**.

## SonarCloud (opcional)

1. Entra en [SonarCloud](https://sonarcloud.io) y vincula el repositorio.
2. Copia el **Project Key** y el **Organization** y rellena `sonar-project.properties` (o configura en la UI).
3. En el repo de GitHub: **Settings → Secrets → Actions** → New repository secret → nombre `SONAR_TOKEN`, valor = token de SonarCloud.

Si no configuras `SONAR_TOKEN`, el job **SonarCloud** fallará; está con `continue-on-error: true` para no bloquear el resto del pipeline.

## Notas

- **pip-audit**: si encuentra vulnerabilidades conocidas en `requirements.txt`, el job puede fallar. Revisa y actualiza dependencias.
- **OWASP Dependency-Check**: la primera ejecución descarga la base NVD (puede tardar varios minutos).
- **ZAP**: el servidor se inicia en el job; si no arranca (p. ej. falta `public.pem`), el escaneo puede fallar (job con `continue-on-error`).
