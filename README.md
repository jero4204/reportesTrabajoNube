# Reporte Bicicletas

Microservicio en Python (FastAPI) para generar reportes en PDF desde Mongo Atlas.

## Endpoints

- `/reporte` → Devuelve un PDF con:
  - Línea de tiempo de ingresos
  - Distribución Compra vs Alquiler
  - Distribución por tipo de bicicleta
  - Totales de ingresos

## Variables de entorno

- `MONGO_URI` → URI de conexión a Mongo Atlas.

## Deploy en OpenShift (ROSA)

```bash
oc new-project reportes-bicis
oc new-app python:3.13-ubi9~https://github.com/<usuario>/<repo>.git --name=reporte-bicis
oc set env deployment/reporte-bicis MONGO_URI="mongodb+srv://..."
oc expose svc/reporte-bicis
oc get route reporte-bicis
