# Guía de Despliegue - ActIA

Este documento detalla la arquitectura de despliegue en producción para la aplicación **ActIA**, especificando dónde está corriendo cada servicio, cómo están configurados y cómo solucionar los problemas de integración más comunes (CORS, URLs, etc.).

---

## 🏗️ Arquitectura de Despliegue (Híbrida)

Para asegurar la estabilidad, escalabilidad y compatibilidad de la aplicación con entornos serverless y persistentes, se optó por un modelo de **despliegue híbrido**:

```
┌────────────────────────────────┐       ┌─────────────────────────────────┐
│     FRONTEND (React + Vite)    │ ────> │        BACKEND (FastAPI)        │
│    Desplegado en: VERCEL       │       │      Desplegado en: RENDER      │
│  https://act-ia.vercel.app     │       │    https://actia.onrender.com   │
└────────────────────────────────┘       └─────────────────────────────────┘
```

1. **Frontend (Vercel):** Se sirve como una aplicación de página única (SPA) estática optimizada y distribuida a nivel global.
2. **Backend (Render):** Se ejecuta en un contenedor persistente de Docker para dar soporte al almacenamiento de trabajos en memoria (`InMemoryJobStore`) y permitir la ejecución de hilos asíncronos en segundo plano sin congelamientos del runtime.

---

## 🔗 Enlaces y Direcciones de Producción

* **Aplicación Web (Frontend):** [https://act-ia.vercel.app/](https://act-ia.vercel.app/)
* **API de Producción (Backend):** [https://actia.onrender.com/](https://actia.onrender.com/)
* **Ruta Base de la API (Vite):** `https://actia.onrender.com/api/v1`
* **Prueba de Liveness (Healthcheck):** [https://actia.onrender.com/api/v1/health](https://actia.onrender.com/api/v1/health)

---

## ⚙️ Configuración y Variables de Entorno

### 1. Frontend (Vercel)
En la configuración del proyecto en el dashboard de Vercel, se deben establecer los siguientes parámetros:

* **Directorio Raíz:** `frontend`
* **Framework Preset:** `Vite`
* **Comando de Build:** `npm run build`
* **Directorio de Output:** `dist`
* **Variables de Entorno:**
  * `VITE_API_BASE_URL`: `https://actia.onrender.com/api/v1` *(⚠️ IMPORTANTE: Sin barra diagonal `/` al final)*

### 2. Backend (Render)
En la sección **Environment** del servicio web en el panel de control de Render, se deben configurar las siguientes variables:

* **Directorio Raíz:** `backend`
* **Runtime:** `Docker` (Render detecta automáticamente el [Dockerfile](file:///c:/Users/SOPORTES%20JPVM/Documents/Personal%20Proyects/ActIA/backend/Dockerfile))
* **Variables de Entorno:**
  * `CORS_ORIGINS`: `http://localhost:5173,https://act-ia.vercel.app` *(⚠️ Permite peticiones tanto del entorno de desarrollo local como del frontend en producción, separadas por coma y sin barra `/` al final)*
  * `ADAPTER_MODE`: `real`
  * `ANALYSIS_PROVIDER`: `assemblyai` *(o `speechmatics`, recomendado para hosting gratuito/CPU sin GPU)*
  * `ASSEMBLYAI_API_KEY`: *(Tu API key de AssemblyAI)*
  * `GEMINI_API_KEY`: *(Tu API key de Google AI Studio)*

---

## 🚨 Gotchas y Resolución de Problemas Frecuentes

### 1. Error de CORS (`CORS Missing Allow Origin`)
Si el navegador arroja errores de CORS al intentar realizar una transcripción, verifica lo siguiente:
* **Falta del origen en `CORS_ORIGINS`:** Asegúrate de que el origen exacto desde el que haces la petición esté listado en la variable `CORS_ORIGINS` del backend. Si estás probando la web de producción, debe incluir `https://act-ia.vercel.app`. Si pruebas en local, debe incluir `http://localhost:5173`.
* **Barra diagonal al final (`/`):** El navegador envía la cabecera `Origin` sin barra diagonal (ej. `https://act-ia.vercel.app`). Si configuraste la variable con la barra al final (`https://act-ia.vercel.app/`), el backend la rechazará por no coincidir exactamente.
* **Redespliegue pendiente:** Cualquier cambio en las variables de entorno de Render requiere guardar los cambios y verificar que se complete un redespliegue manual o automático exitoso para que FastAPI actualice su estado.

### 2. Doble barra diagonal en llamadas a la API
Si configuras `VITE_API_BASE_URL` con una barra final (ej. `https://actia.onrender.com/api/v1/`), las peticiones se resolverán como `.../api/v1//transcriptions/`. 
FastAPI responderá con un redireccionamiento automático (`307` o `308`) para normalizar la URL. Durante esta redirección, el navegador perderá las cabeceras CORS de origen y la petición fallará. **Mantén siempre la URL sin `/` final**.

### 3. Arranque en frío (Cold Start) en Render
Si utilizas el plan gratuito de Render, el contenedor se apagará tras 15 minutos de inactividad. La primera petición que despierte el backend puede tardar hasta 50 segundos en responder. Durante este tiempo, es probable que la petición del frontend falle o expire con un error que el navegador interpretará como un problema de CORS (ya que el balanceador de carga de Render devuelve respuestas de error HTTP 502/504 sin cabeceras CORS).
* *Recomendación:* Visita directamente `https://actia.onrender.com/api/v1/health` en el navegador para despertar el servicio antes de usar la aplicación frontend.
