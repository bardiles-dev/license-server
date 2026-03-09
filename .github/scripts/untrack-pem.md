# Dejar de trackear .pem y keys (mantenerlos solo en local)

Cuando el remoto tiene commits con `.pem` o `keys/` y quieres **seguir teniendo esos archivos en tu proyecto** pero **que no estén en el repositorio**.

## 1. Traer los cambios del remoto (obligatorio para poder hacer push)

```powershell
git fetch origin
git pull origin main --no-rebase
```

Así integras lo que hay en GitHub; si allí había .pem, tras el pull pueden aparecer en tu árbol (pero ya no los volverás a subir en el paso 3).

## 2. Quitarlos del índice (siguen en disco, dejan de estar en Git)

Desde la raíz del repo:

```bash
# Quitar del tracking (los archivos siguen en tu carpeta)
git rm -r --cached license-authority/keys/ 2>nul
git rm --cached license-server/public.pem 2>nul
git rm --cached license-authority/*.pem 2>nul
git rm --cached "*.pem" 2>nul
```

En PowerShell puedes usar:

```powershell
git rm -r --cached license-authority/keys/ 2>$null; $?
git rm --cached license-server/public.pem 2>$null; $?
Get-ChildItem -Recurse -Filter "*.pem" | ForEach-Object { git rm --cached $_.FullName 2>$null }
```

O más simple (quita todo lo que coincida con .pem en el índice):

```bash
git ls-files "*.pem" "**/keys/*" | ForEach-Object { git rm --cached $_ }
```

## 3. Commit y push

```powershell
git add .
git commit -m "chore: stop tracking .pem and keys (keep locally only)"
git push origin main
```

A partir de aquí, `.gitignore` evita que vuelvan a añadirse; los `.pem` y `keys/` solo existen en tu máquina y no se suben al repo.
