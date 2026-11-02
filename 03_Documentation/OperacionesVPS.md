# Operaciones del VPS — referencia rápida para cualquier sesión de Claude Code

Si una sesión de Claude Code (en esta carpeta o en cualquier otra de este mismo ordenador) necesita tocar el servidor de producción de JARVIS, esto es lo que necesita saber.

## Acceso

- **Servidor**: Contabo VPS, IP `169.58.156.162`, usuario `jarvis` (sudo sin contraseña).
- **Clave SSH**: `~/.ssh/jarvis_hetzner` (vive en la carpeta de usuario de Windows, no en este repo — cualquier sesión en este PC puede usarla).
- **Conectar**:
```bash
ssh -i ~/.ssh/jarvis_hetzner jarvis@169.58.156.162
```
- **Dominio**: `jarvis.tuhomeoffice.com` (subdominio de un dominio de IONOS ya existente, apunta por A record a la IP de arriba). HTTPS real vía Caddy/Let's Encrypt.

## Qué corre ahí (docker compose en `~/jarvis-deploy/` del servidor)

- `jarvis-deploy-n8n-1` — n8n (editor en `https://jarvis.tuhomeoffice.com/`)
- `mayordomo-postgres` — Postgres 16, db `mayordomo`, user `mayordomo`
- `jarvis-ollama` — Ollama con `llama3.2:3b`
- `jarvis-deploy-caddy-1` — reverse proxy / TLS

La contraseña de Postgres está en `~/jarvis-deploy/.env` del servidor (`POSTGRES_PASSWORD`) — **nunca la guardes en este repo**, léela directamente ahí cuando la necesites:
```bash
ssh -i ~/.ssh/jarvis_hetzner jarvis@169.58.156.162 "cat ~/jarvis-deploy/.env"
```

## Actualizar el estado de un proyecto directamente (sin pasar por Telegram)

Útil para resúmenes largos o multi-proyecto que el bot (ruta "Actualizar Proyecto") no maneja bien — ahí solo detecta un proyecto por mensaje.

La tabla `mayordomo_entidades` es versionada: nunca se hace UPDATE sobre una fila activa, se archiva la vieja y se inserta una nueva versión con el mismo `raiz_id`.

```sql
-- 1. Leer el estado actual
SELECT id, raiz_id, version, atributos FROM mayordomo_entidades
WHERE tipo = 'proyecto' AND nombre = '<Nombre del proyecto>' AND estado = 'activo';

-- 2. Archivar la version vieja
UPDATE mayordomo_entidades SET estado = 'archivado' WHERE id = '<id de la fila leida>';

-- 3. Insertar la nueva version (atributos completo, con los cambios ya aplicados)
INSERT INTO mayordomo_entidades (usuario_id, tipo, nombre, estado, origen, version, version_anterior_id, raiz_id, atributos)
VALUES ('6644696958', 'proyecto', '<Nombre del proyecto>', 'activo', 'claude', <version+1>, '<id viejo>', '<raiz_id>', '<atributos nuevo en JSON>'::jsonb);
```

Ejecutar desde el host vía:
```bash
docker exec mayordomo-postgres psql -U mayordomo -d mayordomo -c "..."
```

## Repo y despliegue de cambios en workflows

- Repo privado: `git@github.com:basaguigar2/Telegram_AGENT.git` (clonado en el servidor en `~/jarvis`, con una deploy key de solo lectura, no la del admin).
- Para desplegar un cambio en un workflow:
```bash
# en local, tras editar el .json en 04_Implementation/n8n_workflows/
git add . && git commit -m "..." && git push

# en el servidor
ssh -i ~/.ssh/jarvis_hetzner jarvis@169.58.156.162 '
cd ~/jarvis && GIT_SSH_COMMAND="ssh -i ~/.ssh/github_deploy -o StrictHostKeyChecking=accept-new" git pull
docker exec jarvis-deploy-n8n-1 n8n import:workflow --input=/data/jarvis/04_Implementation/n8n_workflows/"<nombre del archivo>.json"
'
```
- **Importante**: reimportar un workflow resetea las credenciales de sus nodos (Postgres, Telegram, OAuth, etc.) — no viajan en el JSON. Hay que re-enlazarlas a mano en la interfaz de n8n después de cada reimport.
