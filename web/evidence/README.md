# Capturas reales del informe

Exportá desde `dashboard/portability_operations.pbix` una imagen PNG de cada página con datos sintéticos y guardala aquí con estos nombres:

- `resumen-operativo.png`
- `analisis-demoras.png`
- `evolucion-mensual.png`

Resolución mínima: 1200 × 675 píxeles. Revisá que no aparezcan credenciales, rutas locales ni datos ajenos a la muestra. `npm run build` valida el formato y copia solo las imágenes presentes a la galería. Si falta una, el sitio muestra claramente «Captura pendiente». Las imágenes fuente se pueden versionar para que Vercel las publique con el siguiente despliegue.

El PBIX contiene estas tres páginas con contenido. El diseño del informe todavía necesita la revisión visual descrita en `docs/dashboard_design.md`; exportar capturas no equivale a completar ese rediseño.
