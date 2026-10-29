# JARVIS — instrucciones de proyecto

## Jev en el sitio de afiliados

El sitio de afiliados (tuhomeoffice.com, nicho home office, Amazon Afiliados España) usa la tool `jev_decide` en dos puntos concretos. Fuera de estos dos, aplica el filtro de decisión del CLAUDE.md global antes de proponer usarla.

### 1. Priorizar el siguiente artículo

- Tipo: `choice`.
- Criterios: volumen de búsqueda, intención de compra, competencia.
- Cuándo: al elegir cuál de los temas candidatos se escribe/publica primero.

```json
{
  "state": "Temas candidatos para el siguiente artículo del blog de home office: <lista corta>",
  "questions": {
    "siguiente_articulo": {
      "type": "choice",
      "instructions": "¿Cuál de estos temas conviene publicar primero?",
      "criteria": {
        "volumen": "más búsquedas potenciales es mejor",
        "intencion": "intención de compra alta es mejor",
        "competencia": "menos competencia es mejor"
      }
    },
    "necesita_revision_humana": { "type": "noul", "instructions": "¿La confianza es baja o el caso es ambiguo?" }
  }
}
```

### 2. Filtro antes de publicar

- Tipo: `noul`.
- Pregunta: "¿es thin content o demasiado salesy?"
- Cuándo: con el borrador final de cada artículo, antes de pulsar Publicar en WordPress.
- Pasa el texto completo del artículo en `state`: Jev solo juzga lo que se le pase, no ve el sitio ni el resto del contexto.

```json
{
  "state": "<texto completo del artículo>",
  "questions": {
    "thin_o_salesy": { "type": "noul", "instructions": "¿Es thin content o demasiado salesy?" },
    "necesita_revision_humana": { "type": "noul", "instructions": "¿La confianza es baja o el caso es ambiguo?" }
  }
}
```

### Reglas comunes

- Confianza < 0.7 o error de la tool: decide tú y anótalo en una línea.
- Si el veredicto es "thin/salesy": no publicar; reescribir y volver a pasar el filtro.
- La decisión final de publicar sigue siendo del usuario.
