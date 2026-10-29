import fs from 'fs';
import path from 'path';

// Ruta del volumen montado dentro del contenedor de n8n (ver docker-compose.yml de n8n-autoalojado).
// Si este script se ejecuta en Windows directamente (fuera del contenedor), cambia esto de vuelta
// a la ruta real de Windows.
const base = '/data/levstamp-videos';
const carpetas = fs.readdirSync(base).filter(n => fs.statSync(path.join(base, n)).isDirectory());

let listos = [];
let pendientes = [];

for (const carpeta of carpetas) {
  const manifestPath = path.join(base, carpeta, 'manifest.json');
  if (!fs.existsSync(manifestPath)) continue;
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
  const faltantes = [];
  for (const asset of manifest.assets_required || []) {
    const assetPath = path.join(base, carpeta, asset.path);
    if (!fs.existsSync(assetPath)) faltantes.push(asset.path);
  }
  if (faltantes.length === 0) {
    listos.push({ carpeta, title: manifest.title });
  } else {
    pendientes.push({ carpeta, title: manifest.title, faltantes });
  }
}

console.log(`Total: ${listos.length + pendientes.length} videos. Listos: ${listos.length}. Pendientes de assets: ${pendientes.length}.`);
console.log('');
for (const p of pendientes) {
  console.log(`${p.carpeta} | ${p.title} | falta: ${p.faltantes.join(', ')}`);
}
