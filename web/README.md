# Portfolio web

Web estática y función serverless para mostrar el desarrollo del pipeline. La construcción genera `public/data/summary.json` desde los CSV versionados; una nueva versión del dataset se refleja al volver a construir y desplegar.

## Despliegue en Vercel

1. Importar el repositorio `SouthClvbDev/portability-data-pipeline` en Vercel.
2. Elegir `web` como **Root Directory**. Framework Preset: **Other**. Build Command: `npm run build`. Output Directory: `public`.
3. Desplegar. No se necesita base PostgreSQL en Vercel: esta web usa un resumen derivado de los CSV públicos. El pipeline completo sigue ejecutándose localmente o en CI.
4. Opcional: agregar `OPENAI_API_KEY` como variable de entorno de servidor en Vercel y volver a desplegar. `OPENAI_MODEL` permite cambiar el modelo; por defecto se usa `gpt-4.1-mini`. No crear variables con prefijo `NEXT_PUBLIC_` ni poner la clave en archivos Git.
5. Revisar el costo y establecer un límite de gasto en el proveedor del modelo antes de habilitar el modo LLM en un sitio público. El modo determinista no consume API.

## Desarrollo local

```bash
cd web
npm ci
npm run build
npm test
npx vercel dev
```

`vercel dev` requiere la CLI y una sesión de Vercel; para revisar solo la interfaz se puede servir `public/` con un servidor estático, aunque el chat necesita la función `/api/chat`.

## Alcance de las respuestas

El modo determinista responde a total, abiertos/cerrados, estados, SLA, canal, equipo y evolución mensual. La función lee únicamente el resumen generado; no consulta un PostgreSQL privado ni ejecuta SQL sugerido por el visitante. El modo LLM está desactivado sin clave y sus respuestas deben verificarse contra los indicadores. El dataset es sintético y registra estado actual, no historial de transiciones.
