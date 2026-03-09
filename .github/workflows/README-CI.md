# CI / GitHub Actions

Workflow: **`.github/workflows/ci.yml`**

## Jobs

| Job | Descripción |
|-----|-------------|
| **Build verification** | Instala dependencias de cada proyecto y comprueba que `app.main:app` importe correctamente. |
| **Code quality** | Ruff check + Ruff format check sobre ambos proyectos. |
| **Secret scanning** | Gitleaks: detección de secretos y credenciales en el repositorio. |
| **Trivy (repository)** | Escaneo del repositorio (fs). SARIF a Security tab + artifact `trivy-repo-reports` (SARIF + tabla). |
| **Trivy (dependencies)** | Trivy sobre el entorno Python tras instalar dependencias (por proyecto). Artifact `trivy-deps-<proyecto>`. |
| **Trivy (container)** | Construye la imagen Docker de `license-server` y la escanea con Trivy (vulnerabilidades + config). Artifact `trivy-container-license-server` + SARIF a Security. |
| **Supply chain security** | Dependency review en PRs (vulnerabilidades en dependencias de los manifest cambiados). |
| **Dependency audit (pip-audit)** | Vulnerabilidades en dependencias Python (PyPI) por proyecto. |
| **OWASP Dependency-Check** | Análisis CVE/NVD con imagen Docker. SARIF a Security + artifact `owasp-dependency-check-reports`. |
| **SAST (Bandit)** | Análisis estático de seguridad sobre el código Python. |
| **DAST (OWASP ZAP)** | Escaneo baseline + full scan contra license-server (solo en push a `main`). **Reporte HTML** subido como artifact `dast-zap-report`. |

## Reportes y artefactos

- **Artifacts (descargables)**  
  En **Actions** → run → **Artifacts** encontrarás: `trivy-repo-reports`, `trivy-deps-<proyecto>`, `trivy-container-license-server`, `owasp-dependency-check-reports`, `dast-zap-report` (solo en push a `main`).

- **SARIF (Security tab)**  
  CodeQL Action **v4** sube SARIF de Trivy (repo + contenedor) y OWASP Dependency-Check a **Security** → **Code security**.

## Secrets

- **`SONAR_TOKEN`**: solo si usas SonarCloud (job comentado por defecto).
- **Gitleaks**: usa `GITHUB_TOKEN`; no requiere secret adicional para uso estándar.

## Notas

- **pip-audit**: no hace fallar el job; revisar hallazgos y actualizar dependencias.
- **OWASP Dependency-Check**: primera ejecución puede tardar (descarga NVD).
- **ZAP**: el servidor se levanta en el job; si falla (p. ej. falta `public.pem`), el escaneo puede fallar (job con `continue-on-error`).
- **Supply chain**: solo se ejecuta en **pull_request**.
- **DAST y reporte HTML**: solo en **push** a `main`.
