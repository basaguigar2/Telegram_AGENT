# Infraestructura para JARVIS: PC actual vs Raspberry Pi vs VPS vs Oracle Free Tier

Fecha del estudio: octubre 2026. Los precios de VPS están en movimiento este año (ver notas), así que antes de pagar nada, confirma el precio en vivo en la web del proveedor.

## 0. Punto de partida real

Hoy todo corre en tu PC Windows de siempre (`docker-compose.yml` en `BasBusiness/n8n-autoalojado`), expuesto a internet vía ngrok. La pregunta no es solo "VPS vs Raspberry Pi" en abstracto — es si merece la pena salir de tu PC principal, y hacia dónde.

Dos problemas de seguir ahí, independientes del coste:
- **Aislamiento**: si algo en el contenedor de n8n se compromete (plugin malicioso, dependencia de npm, lo que sea), está en la misma máquina que tus archivos personales y sesiones de navegador. Un servidor dedicado (RPi o VPS) no tiene ese problema.
- **Estabilidad**: Windows Update puede reiniciar la máquina sin avisarte: se cae el contenedor, se cae la rutina de las 6:30, se cae el bot. Docker Desktop en Windows además corre dentro de una VM (WSL2), con más overhead que Docker nativo en Linux.

Esto ya es un argumento para moverse, sea a RPi o a VPS.

## 1. Raspberry Pi 5 (8GB)

**Coste de hardware (el dato que más ha cambiado):** los precios de RPi 5 han subido fuerte en 2026 por la escasez de memoria RAM que está golpeando a toda la industria — una fuente lo sitúa en +70% respecto a antes. Encontré precios en tiendas españolas entre **160€ y 210€** solo por la placa de 8GB, con stock intermitente (RS Online la tenía agotada temporalmente). Suma caja, fuente de alimentación de calidad, y un SSD/NVMe (la SD se degrada rápido con Postgres escribiendo constantemente) — cuenta unos **220-260€ de golpe**.

**Electricidad (el dato que YA NO es el problema):** un RPi 5 consume entre 5-10W corriendo n8n+Postgres+Ollama de forma modesta. A 24h/día, 30 días, eso son 3,6-7,2 kWh/mes. Con el precio de la luz en España rondando 0,15-0,20 €/kWh este año (varía mucho día a día, no hay un promedio anual fiable todavía), hablamos de **1-1,5€/mes**. Literalmente insignificante — ni se acerca a ser el factor decisivo que a veces se piensa.

**El problema real del RPi no es el coste, es la potencia:** Ollama con llama3.2:3b en CPU ya es lento; en un ARM Cortex-A76 a 2.4GHz sin GPU, bastante más. Si n8n, Postgres y Ollama compiten por los mismos 4 núcleos a la vez (ej. la rutina de las 6:30 corriendo mientras alguien te escribe por Telegram), vas a notarlo. Tampoco escala: si algún día quieres más proyectos, más automatizaciones, el único plan es comprar otra placa.

**Fiabilidad:** depende de tu internet y tu luz de casa. Un corte de luz tira el bot entero (sin UPS). La SD/microSD es un punto de fallo clásico en RPi con bases de datos — por eso conviene NVMe, pero eso son otros 30-40€ más.

## 2. VPS

### 2.1 Qué necesitas en la práctica

Para n8n + Postgres + Ollama (aunque Llama solo haga tareas acotadas, el modelo igual necesita RAM cargada) el mínimo cómodo es **4 vCPU / 8GB RAM**, ya que 2GB o 4GB se queda corto en cuanto Ollama entra en juego a la vez que Postgres. Evita planes "burstable"/con CPU compartida agresiva si puedes — quieres rendimiento consistente para que la rutina de las 6:30 no se arrastre.

### 2.2 Proveedores (precios con bastante ruido este año — verifica en la web antes de decidir)

| Proveedor | Plan aprox. 4 vCPU / 8GB | Precio aproximado/mes | Nota |
|---|---|---|---|
| **Hetzner Cloud** | CX33 | ~6,50€ | Hetzner subió precios entre 30-37% en abril 2026; algunos planes "Cost-Optimized" aparecían agotados en septiembre. Mira el panel en vivo. |
| **Contabo** | Cloud VPS 10 / VPS 4 | ~5-7€ (más barato aún con compromiso de 12-24 meses) | Históricamente el más barato por RAM, aunque reseñas señalan soporte más lento y SSD no siempre NVMe en gama baja. |
| **DigitalOcean** | Droplet 4GB/2vCPU | ~24-48 $ | Para llegar a 8GB/4vCPU subes de precio notablemente — DO es más caro por recurso que Hetzner/Contabo, pero con mejor reputación de estabilidad y paneles. |
| **IONOS** | VPS Linux L (4 cores/8GB/240GB) | ~15$/mes estándar (promo ~10$/mes los primeros 6 meses) | Grupo alemán serio (1&1 IONOS, cotiza en bolsa), datacenters en la UE. Trae de serie DDoS Protect básico, IPv6 e históricamente backups incluidos en según el plan — revisa cuáles aplican al tuyo. Opción tan válida como Hetzner/Contabo, sin ser la más barata. |
| **Hostinger** | KVM 4 (≈4 vCPU/16GB) | ~13$/mes SOLO en precio de entrada con contrato largo (24-48 meses) — la renovación puede duplicar o más ese precio | Pensada para quien ya usa Hostinger de hosting compartido y sube a VPS. El precio llamativo es un anzuelo de renovación: una review calculó que renovando año a año sale más caro a 3 años que pagar 4 años de golpe. Si quieres margen para cambiar de proveedor o redimensionar sin ataduras (como pediste con "escalabilidad"), este es el que menos encaja. |

### 2.2.1 Hetzner vs Contabo, letra pequeña (lo que no se ve a simple vista en el precio)

Ojo: el plan Cost-Optimized de Hetzner a 5,99$/mes (2 vCPU, 4GB, 40GB) NO es el mismo escalón que el Contabo de 4 vCPU/8GB a 5,28$/mes (24 meses) — tiene la mitad de recursos. El comparable real en Hetzner es el de 4 vCPU/8GB (gama CX33/CPX, ~7-8€).

| | Hetzner | Contabo |
|---|---|---|
| Puerto / velocidad | 1 Gbps real, compartido | 200 Mbit/s — tope de plan, no el puerto físico |
| Tráfico incluido | 20 TB/mes en UE, excedente ≈1€/TB | "Ilimitado" con fair-use (sin cifra concreta) |
| IPv4 | NO incluida — 0,50€/mes aparte | Incluida en el precio base |
| Snapshot | Pago por GB/mes almacenado, sin cuota gratis clara | 1 snapshot incluido |
| Backup automático | Add-on = 20% del precio del servidor | +2$/mes fijo |
| Disponibilidad | Reportes de mediados de octubre 2026 mostraban los 8 planes Cost-Optimized como "no disponible" en algunos momentos — confirmar en checkout antes de decidir | Sin reportes de indisponibilidad |

Con esto: Hetzner gana en red (puerto y tráfico reales, sin letra pequeña), Contabo da más de entrada en snapshot e IPv4 incluida. El backup automático, en términos absolutos, sale más barato en Hetzner para un plan pequeño por ser porcentaje y no fijo.

**Pero en la práctica, para esta carga de trabajo, tráfico y puerto no pesan nada en la decisión.** Lo que mueve el sistema (bot de Telegram, llamadas a Jev/Claude/Calendar, n8n↔Postgres↔Ollama interno) son unos pocos MB/mes como mucho — ni de lejos cerca de ningún límite de ningún proveedor, y la velocidad de puerto solo importa moviendo archivos pesados, que aquí no se mueven por el VPS. El criterio real para decidir es RAM/CPU (por Ollama) + precio puro, y ahí, para el mismo escalón de 4vCPU/8GB, Contabo (~5€, 24 meses) le gana claramente a Hetzner (~9€) — con el matiz de que Contabo sube a ~6,60$ al acabar esos 24 meses, y no incluye IPv4 gratis Hetzner.

**Seguridad en un VPS (lo que harías tú, no el proveedor):** firewall (UFW o el firewall nativo del proveedor) cerrando todo salvo 22/443, SSH solo por clave (nunca contraseña), fail2ban, actualizaciones automáticas de seguridad del sistema, Postgres SIN puerto expuesto al host igual que ahora, y — esto es importante — sustituir el túnel de ngrok por un dominio propio + reverse proxy (Caddy o Nginx) con TLS real vía Let's Encrypt, o una Cloudflare Tunnel con política de acceso. Eso resuelve de forma más limpia lo que ya tocaste ("cambiado lo de ngrok") sin depender de un túnel hacia tu casa.

### 2.3 Oracle Cloud "Always Free" (Ampere ARM) — la opción a coste cero, con matices

Oracle ofrece (o ofrecía) instancias ARM Ampere gratis para siempre: hasta hace poco, 4 OCPU / 24GB RAM / 200GB disco, repartibles en hasta 4 VMs. **Dato importante y no verificado del todo:** varias fuentes de 2026 dicen que Oracle redujo esa asignación a 2 OCPU / 12GB sin anuncio oficial claro, y que la aplicación es inconsistente. Además es conocido que:
- Conseguir que te deje crear la instancia gratuita en ARM a veces falla por "falta de capacidad" en la región, durante semanas.
- Hay historial de cuentas gratuitas de Oracle suspendidas o instancias terminadas sin aviso claro.

2 o 4 OCPU / 12-24GB en ARM es de sobra para esta carga, y el precio (cero) es imbatible — pero dado que quieres que esto sea fiable para tu día a día (briefing diario, recordatorios), no lo pondría como única pieza de producción. Sí tiene sentido probarlo en paralelo sin coste, como entorno de pruebas o como segunda pieza más adelante.

## 3. Comparativa de coste total

| Opción | Coste inicial | Coste mensual recurrente | Rendimiento Ollama | Fiabilidad | Escalabilidad |
|---|---|---|---|---|---|
| PC actual (status quo) | 0€ | ~4-6€ electricidad (estimado, PC de sobremesa 24/7) | Buena (CPU x86 de escritorio) | Baja (reinicios de Windows, WSL2) | Ninguna real |
| Raspberry Pi 5 8GB | ~220-260€ | ~1-2€ electricidad | Floja (ARM sin GPU, 4 núcleos compartidos) | Media (sin UPS, SD/NVMe) | Ninguna (comprar más placas) |
| VPS 4vCPU/8GB (Hetzner/Contabo) | 0€ | ~5-7€ | Buena/aceptable (vCPU dedicada) | Alta (datacenter, SLA) | Alta (resize con un clic) |
| Oracle Free Tier ARM | 0€ | 0€ | Aceptable (pero ARM) | Incierta (riesgo de suspensión/capacidad) | Limitada por el free tier |

## 4. Recomendación

**Salir del PC principal y pasar a un VPS pequeño (4 vCPU/8GB) en Hetzner, Contabo o IONOS** — confirma el precio del día en su web, ronda los 5-7€/mes en Hetzner/Contabo o ~10-15$/mes en IONOS (algo más caro, pero con extras ya incluidos y el peso de ser un grupo alemán establecido). **Descartaría Hostinger** para este uso: el precio de entrada tienta, pero está atado a contratos largos con una renovación que puede duplicar el coste — justo lo contrario de la flexibilidad que buscas. Razones, en orden de peso:
1. Aísla el sistema de tus archivos/sesiones personales — el motivo de seguridad más sólido, más allá de cualquier coste.
2. La Raspberry Pi 5 ya no es la opción "barata": con los precios actuales (~220-260€ de entrada por la escasez de RAM) y peor rendimiento para Ollama, pierde frente a un VPS que cuesta lo mismo en electricidad pero sin desembolso inicial y con mucho mejor rendimiento/fiabilidad.
3. Resuelve de forma más limpia el tema ngrok (dominio propio + TLS real en vez de túnel hacia casa).
4. Escalable: si mañana quieres meter más proyectos o más carga, subes de plan sin comprar hardware nuevo.

Opcional y sin coste: levanta también una instancia ARM gratuita en Oracle en paralelo, como entorno de pruebas o pieza secundaria — pero no como base única, por el riesgo de que Oracle te la quite sin aviso.

## Fuentes consultadas

- [Hetzner's 2026 Price Increase](https://findstack.com/resources/hetzner-price-increase-2026)
- [Hetzner Cloud Cost Optimized plans](https://www.bitdoze.com/md/hetzner-cloud-cost-optimized-plans.md)
- [Hetzner Cloud Review 2026](https://www.bitdoze.com/md/hetzner-cloud-review.md)
- [Contabo pricing (aggregated)](https://www.temperstack.com/plans/contabo/)
- [Contabo Pricing 2026](https://onedollarvps-com.pages.dev/pricing/contabo-pricing)
- [Setup Always Free VPS with 4 OCPU/24GB — Oracle Cloud Guide 2026](https://medium.com/@imvinojanv/setup-always-free-vps-with-4-ocpu-24gb-ram-and-200gb-storage-the-ultimate-oracle-cloud-guide-bed5cbf73d34)
- [Oracle Cloud Free Tier changes 2026](https://terminalbytes.com/oracle-cloud-free-tier-changes-2026)
- [DigitalOcean 2026 Pricing Update](https://prjs-astro.pages.dev/blog/2026-03-08_digitalocean-_3)
- [DigitalOcean Pricing 2026: Droplet Costs, Backups and Hidden Fees](https://diyai.io/ai-tools/hosting/digitalocean-pricing/)
- [IONOS VPS Review 2026](https://bestusavps.pages.dev/reviews/ionos)
- [Compare IONOS Plans: Prices vs vCPUs](https://www.vpsbenchmarks.com/intelligence_chats/529d045f8d)
- [Hostinger VPS Review 2026](https://bestusavps.pages.dev/reviews/hostinger-vps)
- [VPS Comparison 2026 — RamNode vs Hostinger](https://www.ramnode.com/ramnode-hostinger)
- [Precio de la luz — Selectra, octubre 2026](https://selectra.es/energia/noticias/precio-luz/2026-10-21)
- [Raspberry Pi 2026: precios suben 70%, guía de compra](https://ecosistemastartup.com/?p=77350)
- [Raspberry Pi 5 8GB — RS Online España](https://es.rs-online.com/web/p/raspberry-pi/0219255)
