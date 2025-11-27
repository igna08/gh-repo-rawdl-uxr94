# API de Reportes - Documentación para Frontend

Esta documentación describe los endpoints de reportes disponibles para integrar en tu frontend.

## Tabla de Contenidos

1. [Overview](#overview)
2. [Autenticación](#autenticación)
3. [Endpoints Disponibles](#endpoints-disponibles)
4. [Manejo de Fechas](#manejo-de-fechas)
5. [Control de Acceso](#control-de-acceso)
6. [Ejemplos de Uso](#ejemplos-de-uso)
7. [Schemas de Respuesta](#schemas-de-respuesta)
8. [Manejo de Errores](#manejo-de-errores)
9. [Mejores Prácticas](#mejores-prácticas)

---

## Overview

La API de reportes proporciona endpoints para obtener estadísticas y análisis del sistema de gestión de activos escolares. Incluye:

- **Reportes de Activos**: Estadísticas de inventario, distribución por estado/categoría, valores totales
- **Reportes de Incidentes**: Análisis de incidentes, tiempos de resolución, activos problemáticos
- **Reporte Overview**: Vista integral combinando todas las métricas

Todos los reportes soportan filtrado por rango de fechas y escuela.

---

## Autenticación

Todos los endpoints requieren autenticación mediante JWT token.

### Headers Requeridos

```javascript
{
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}
```

### Obtener el Token

Usa el endpoint de login para obtener el token:

```javascript
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password'
  })
});

const { access_token } = await response.json();
```

---

## Endpoints Disponibles

Base URL: `/api/reports`

### 1. Reporte de Activos (JSON)

```
GET /api/reports/assets
```

Obtiene estadísticas completas de activos con desgloses por estado, categoría y escuela.

**Parámetros de Query:**
- `start_date` (opcional): Fecha de inicio en formato ISO 8601 (ej: "2025-01-01")
- `end_date` (opcional): Fecha de fin en formato ISO 8601
- `preset` (opcional): Rango predefinido ("today", "week", "month", "quarter", "year", "all_time")
- `school_id` (opcional): UUID de la escuela (solo para Super Admin)

**Response:** JSON (`AssetReport`)

---

### 2. Reporte de Incidentes (JSON)

```
GET /api/reports/incidents
```

Obtiene análisis completo de incidentes incluyendo métricas de resolución y activos problemáticos.

**Parámetros de Query:**
- `start_date` (opcional): Fecha de inicio en formato ISO 8601
- `end_date` (opcional): Fecha de fin en formato ISO 8601
- `preset` (opcional): Rango predefinido
- `school_id` (opcional): UUID de la escuela (solo para Super Admin)

**Response:** JSON (`IncidentReport`)

---

### 3. Reporte Overview (JSON)

```
GET /api/reports/overview
```

Obtiene un reporte integral combinando activos e incidentes en una sola respuesta.

**Parámetros de Query:**
- `start_date` (opcional): Fecha de inicio en formato ISO 8601
- `end_date` (opcional): Fecha de fin en formato ISO 8601
- `preset` (opcional): Rango predefinido
- `school_id` (opcional): UUID de la escuela (solo para Super Admin)

**Response:** JSON (`ReportsOverview`)

---

## 🎯 Exportación a PDF (NUEVO)

### 4. Exportar Reporte de Activos (PDF)

```
GET /api/reports/assets/export
```

**Descarga un archivo PDF** con el reporte completo de activos formateado profesionalmente.

**Parámetros de Query:**
- `start_date` (opcional): Fecha de inicio en formato ISO 8601
- `end_date` (opcional): Fecha de fin en formato ISO 8601
- `preset` (opcional): Rango predefinido
- `school_id` (opcional): UUID de la escuela (solo para Super Admin)

**Response:** Archivo PDF descargable
- **Filename:** `reporte_activos_YYYYMMDD_HHMMSS.pdf`
- **Content-Type:** `application/pdf`

**Contenido del PDF:**
- 📊 Resumen ejecutivo con métricas clave
- 📦 Distribución de activos por estado (tabla)
- 🏷️ Distribución por categoría (tabla)
- 🏫 Distribución por escuela (tabla)
- 💎 Top 10 activos más valiosos

---

### 5. Exportar Reporte de Incidentes (PDF)

```
GET /api/reports/incidents/export
```

**Descarga un archivo PDF** con el análisis completo de incidentes.

**Parámetros de Query:**
- `start_date` (opcional): Fecha de inicio en formato ISO 8601
- `end_date` (opcional): Fecha de fin en formato ISO 8601
- `preset` (opcional): Rango predefinido
- `school_id` (opcional): UUID de la escuela (solo para Super Admin)

**Response:** Archivo PDF descargable
- **Filename:** `reporte_incidentes_YYYYMMDD_HHMMSS.pdf`
- **Content-Type:** `application/pdf`

**Contenido del PDF:**
- ⚠️ Distribución de incidentes por estado
- ⏱️ Tiempo promedio de resolución
- 🔧 Activos con más incidentes
- 📋 Listado de incidentes recientes

---

### 6. Exportar Reporte General (PDF)

```
GET /api/reports/overview/export
```

**Descarga un archivo PDF** con el reporte integral combinando activos e incidentes.

**Parámetros de Query:**
- `start_date` (opcional): Fecha de inicio en formato ISO 8601
- `end_date` (opcional): Fecha de fin en formato ISO 8601
- `preset` (opcional): Rango predefinido
- `school_id` (opcional): UUID de la escuela (solo para Super Admin)

**Response:** Archivo PDF descargable
- **Filename:** `reporte_general_YYYYMMDD_HHMMSS.pdf`
- **Content-Type:** `application/pdf`

**Contenido del PDF:**
- **Sección Activos:** Todas las métricas y tablas de activos
- **Sección Incidentes:** Todas las métricas y tablas de incidentes
- Formato profesional de múltiples páginas

---

## Manejo de Fechas

### Formatos Aceptados

**Fechas ISO 8601:**
- Formato: `YYYY-MM-DD` (ej: "2025-01-15")
- También acepta: `YYYY-MM-DDTHH:MM:SSZ` (ej: "2025-01-15T10:30:00Z")

### Opciones Preset

En lugar de especificar fechas manualmente, puedes usar presets:

| Preset | Descripción | Rango |
|--------|-------------|-------|
| `today` | Hoy | Últimas 24 horas |
| `week` | Semana | Últimos 7 días |
| `month` | Mes | Últimos 30 días |
| `quarter` | Trimestre | Últimos 90 días |
| `year` | Año | Últimos 365 días |
| `all_time` | Todo el tiempo | Sin filtro de fecha |

### Comportamiento por Defecto

Si no especificas fechas ni preset:
- **Default**: Últimos 30 días

### Prioridad de Filtros

1. Si existe `preset` → Usar preset
2. Si existen `start_date` o `end_date` → Usar fechas explícitas
3. Si no hay ninguno → Usar default (30 días)

---

## Control de Acceso

### Roles y Permisos

| Endpoint | Super Admin | School Admin | Teacher | Inventory Manager |
|----------|-------------|--------------|---------|-------------------|
| `/reports/assets` | ✅ Todas escuelas | ✅ Su escuela | ✅ Su escuela | ✅ Su escuela |
| `/reports/incidents` | ✅ Todas escuelas | ✅ Su escuela | ✅ Su escuela | ✅ Su escuela |
| `/reports/overview` | ✅ Todas escuelas | ✅ Su escuela | ✅ Su escuela | ✅ Su escuela |

### Filtrado Automático por Escuela

- **Super Admin**: Puede ver todas las escuelas o filtrar por una específica usando `school_id`
- **Otros roles**: Automáticamente filtrados a su escuela asignada (el parámetro `school_id` se ignora)

---

## Ejemplos de Uso

### Ejemplo 1: Descargar Reporte PDF de Activos

```javascript
async function downloadAssetReportPDF(preset = 'month') {
  const token = localStorage.getItem('token');

  const response = await fetch(`/api/reports/assets/export?preset=${preset}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  // Convertir respuesta a blob
  const blob = await response.blob();

  // Crear URL temporal para el blob
  const url = window.URL.createObjectURL(blob);

  // Crear elemento <a> temporal para descargar
  const a = document.createElement('a');
  a.href = url;
  a.download = `reporte_activos_${new Date().toISOString().split('T')[0]}.pdf`;
  document.body.appendChild(a);
  a.click();

  // Limpiar
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

// Uso
downloadAssetReportPDF('month'); // Descarga PDF del último mes
```

### Ejemplo 2: Botón de Descarga en React

```javascript
function DownloadReportButton({ reportType = 'assets', preset = 'month' }) {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      const response = await fetch(`/api/reports/${reportType}/export?preset=${preset}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Error al descargar el reporte');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reporte_${reportType}_${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

    } catch (error) {
      console.error('Error:', error);
      alert('Error al descargar el reporte');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button onClick={handleDownload} disabled={loading}>
      {loading ? 'Descargando...' : '📄 Descargar PDF'}
    </button>
  );
}

// Uso
<DownloadReportButton reportType="assets" preset="month" />
<DownloadReportButton reportType="incidents" preset="week" />
<DownloadReportButton reportType="overview" preset="year" />
```

### Ejemplo 3: Abrir PDF en Nueva Pestaña (Sin Descargar)

```javascript
async function openAssetReportPDF(preset = 'month') {
  const token = localStorage.getItem('token');

  const response = await fetch(`/api/reports/assets/export?preset=${preset}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);

  // Abrir en nueva pestaña
  window.open(url, '_blank');

  // Limpiar después de un tiempo (el PDF ya está abierto)
  setTimeout(() => window.URL.revokeObjectURL(url), 1000);
}
```

### Ejemplo 4: Obtener Reporte JSON de Activos (Para Dashboards)

```javascript
async function getAssetReport() {
  const token = localStorage.getItem('token');

  const response = await fetch('/api/reports/assets?preset=month', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  console.log('Total Assets:', data.total_assets);
  console.log('Total Value:', data.total_value);
  console.log('By Status:', data.by_status);

  return data;
}
```

### Ejemplo 2: Obtener Reporte de Incidentes (Rango Personalizado)

```javascript
async function getIncidentReport(startDate, endDate) {
  const token = localStorage.getItem('token');

  const params = new URLSearchParams({
    start_date: startDate,  // "2025-01-01"
    end_date: endDate       // "2025-01-31"
  });

  const response = await fetch(`/api/reports/incidents?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  const data = await response.json();
  console.log('Total Incidents:', data.total_incidents);
  console.log('Average Resolution (hours):', data.average_resolution_hours);
  console.log('Unresolved:', data.unresolved_count);

  return data;
}
```

### Ejemplo 3: Obtener Overview Completo (Con Preset)

```javascript
async function getReportsOverview(preset = 'month') {
  const token = localStorage.getItem('token');

  const response = await fetch(`/api/reports/overview?preset=${preset}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  const data = await response.json();

  // Datos de activos
  console.log('Assets:', data.assets);

  // Datos de incidentes
  console.log('Incidents:', data.incidents);

  return data;
}
```

### Ejemplo 4: React Hook Personalizado

```javascript
import { useState, useEffect } from 'react';

function useAssetReport(preset = 'month') {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchReport() {
      try {
        setLoading(true);
        const token = localStorage.getItem('token');

        const response = await fetch(`/api/reports/assets?preset=${preset}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchReport();
  }, [preset]);

  return { data, loading, error };
}

// Uso del hook
function AssetDashboard() {
  const { data, loading, error } = useAssetReport('month');

  if (loading) return <div>Cargando...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Total de Activos: {data.total_assets}</h2>
      <h3>Valor Total: ${data.total_value.toFixed(2)}</h3>
      {/* Renderizar más datos... */}
    </div>
  );
}
```

---

## Schemas de Respuesta

### AssetReport

```json
{
  "total_assets": 450,
  "total_value": 125000.50,
  "by_status": [
    {
      "status": "available",
      "count": 320,
      "total_value": 95000.00
    },
    {
      "status": "in_repair",
      "count": 25,
      "total_value": 8500.00
    },
    {
      "status": "missing",
      "count": 5,
      "total_value": 2500.00
    }
  ],
  "by_category": [
    {
      "category_id": "uuid-here",
      "category_name": "Mobiliario",
      "count": 200,
      "total_value": 60000.00
    },
    {
      "category_id": "uuid-here",
      "category_name": "Electrónica",
      "count": 150,
      "total_value": 50000.00
    }
  ],
  "by_school": [
    {
      "school_id": "uuid-here",
      "school_name": "Escuela Primaria #1",
      "count": 200,
      "total_value": 60000.00
    }
  ],
  "assets_without_template": 10,
  "top_valued_assets": [
    {
      "id": "uuid-here",
      "template_name": "Computadora de Escritorio",
      "serial_number": "SN-12345",
      "value_estimate": 1500.00,
      "status": "available",
      "classroom_id": "uuid-here"
    }
  ],
  "date_range": {
    "start": "2025-10-28T00:00:00Z",
    "end": "2025-11-27T23:59:59Z",
    "preset": "month"
  },
  "generated_at": "2025-11-27T15:30:00Z"
}
```

### IncidentReport

```json
{
  "total_incidents": 45,
  "by_status": [
    {
      "status": "open",
      "count": 15
    },
    {
      "status": "in_progress",
      "count": 10
    },
    {
      "status": "resolved",
      "count": 18
    },
    {
      "status": "closed",
      "count": 2
    }
  ],
  "average_resolution_hours": 24.5,
  "unresolved_count": 25,
  "recent_incidents": [
    {
      "id": "uuid-here",
      "asset_id": "uuid-here",
      "description": "Pantalla rota",
      "status": "open",
      "reported_at": "2025-11-20T10:30:00Z",
      "resolved_at": null,
      "reported_by": "uuid-here"
    }
  ],
  "top_assets_with_incidents": [
    {
      "asset_id": "uuid-here",
      "template_name": "Silla de Escritorio",
      "serial_number": "CH-789",
      "incident_count": 5
    }
  ],
  "date_range": {
    "start": "2025-10-28T00:00:00Z",
    "end": "2025-11-27T23:59:59Z",
    "preset": "month"
  },
  "generated_at": "2025-11-27T15:30:00Z"
}
```

### ReportsOverview

```json
{
  "assets": {
    // AssetReport completo (ver arriba)
  },
  "incidents": {
    // IncidentReport completo (ver arriba)
  },
  "generated_at": "2025-11-27T15:30:00Z"
}
```

---

## Manejo de Errores

### Códigos de Estado HTTP

| Código | Significado | Descripción |
|--------|-------------|-------------|
| `200` | OK | Solicitud exitosa |
| `401` | Unauthorized | Token faltante o inválido |
| `403` | Forbidden | Sin permisos suficientes |
| `422` | Validation Error | Parámetros inválidos |
| `500` | Internal Server Error | Error del servidor |

### Ejemplo de Error Response

```json
{
  "detail": "Could not validate credentials"
}
```

### Manejo de Errores en JavaScript

```javascript
async function getReportWithErrorHandling() {
  try {
    const token = localStorage.getItem('token');

    const response = await fetch('/api/reports/assets?preset=month', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.status === 401) {
      // Token expirado o inválido - redirigir a login
      window.location.href = '/login';
      return;
    }

    if (response.status === 403) {
      // Sin permisos
      throw new Error('No tienes permisos para ver este reporte');
    }

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Error desconocido');
    }

    const data = await response.json();
    return data;

  } catch (error) {
    console.error('Error fetching report:', error);
    throw error;
  }
}
```

---

## Mejores Prácticas

### 1. Caché de Reportes

Los reportes pueden ser costosos computacionalmente. Considera implementar caché en el frontend:

```javascript
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutos

class ReportCache {
  constructor() {
    this.cache = new Map();
  }

  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;

    const now = Date.now();
    if (now - item.timestamp > CACHE_DURATION) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  set(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }
}

const reportCache = new ReportCache();

async function getAssetReportCached(preset) {
  const cacheKey = `assets-${preset}`;

  // Intentar obtener del caché
  const cached = reportCache.get(cacheKey);
  if (cached) {
    console.log('Using cached data');
    return cached;
  }

  // Si no hay caché, hacer request
  const token = localStorage.getItem('token');
  const response = await fetch(`/api/reports/assets?preset=${preset}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  const data = await response.json();

  // Guardar en caché
  reportCache.set(cacheKey, data);

  return data;
}
```

### 2. Indicadores de Carga

Siempre muestra indicadores de carga mientras se obtienen reportes:

```javascript
function ReportDashboard() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    async function loadReport() {
      setLoading(true);
      try {
        const report = await getAssetReport();
        setData(report);
      } finally {
        setLoading(false);
      }
    }
    loadReport();
  }, []);

  if (loading) {
    return (
      <div className="loading-spinner">
        <span>Cargando reporte...</span>
      </div>
    );
  }

  return <div>{/* Renderizar datos */}</div>;
}
```

### 3. Formateo de Números

Formatea valores monetarios y números grandes:

```javascript
function formatCurrency(value) {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS'
  }).format(value);
}

function formatNumber(value) {
  return new Intl.NumberFormat('es-AR').format(value);
}

// Uso
<div>
  <p>Total de Activos: {formatNumber(data.total_assets)}</p>
  <p>Valor Total: {formatCurrency(data.total_value)}</p>
</div>
```

### 4. Actualización Periódica

Para dashboards en tiempo real, actualiza los datos periódicamente:

```javascript
function LiveReportDashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Cargar inicial
    loadReport();

    // Actualizar cada 5 minutos
    const interval = setInterval(loadReport, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  async function loadReport() {
    const report = await getAssetReport();
    setData(report);
  }

  return <div>{/* Renderizar */}</div>;
}
```

### 5. Visualización de Datos

Usa librerías de gráficos para visualizar los reportes:

```javascript
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

function AssetStatusChart({ statusData }) {
  const COLORS = {
    'available': '#10b981',
    'in_repair': '#f59e0b',
    'missing': '#ef4444',
    'decommissioned': '#6b7280'
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={statusData}
          dataKey="count"
          nameKey="status"
          cx="50%"
          cy="50%"
          outerRadius={100}
          label
        >
          {statusData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[entry.status]} />
          ))}
        </Pie>
      </PieChart>
    </ResponsiveContainer>
  );
}
```

---

## Casos de Uso Comunes

### Dashboard Principal

```javascript
function MainDashboard() {
  const { data, loading } = useReportOverview('month');

  if (loading) return <Loading />;

  return (
    <div className="dashboard">
      <div className="stats-grid">
        <StatCard
          title="Total de Activos"
          value={data.assets.total_assets}
          icon="📦"
        />
        <StatCard
          title="Valor Total"
          value={formatCurrency(data.assets.total_value)}
          icon="💰"
        />
        <StatCard
          title="Incidentes Abiertos"
          value={data.incidents.unresolved_count}
          icon="⚠️"
        />
        <StatCard
          title="Tiempo Promedio Resolución"
          value={`${data.incidents.average_resolution_hours?.toFixed(1) || 0} hrs`}
          icon="⏱️"
        />
      </div>

      <div className="charts-grid">
        <AssetStatusChart data={data.assets.by_status} />
        <IncidentStatusChart data={data.incidents.by_status} />
      </div>
    </div>
  );
}
```

### Selector de Rango de Fechas

```javascript
function DateRangeSelector({ onChange }) {
  const [preset, setPreset] = useState('month');

  const presets = [
    { value: 'today', label: 'Hoy' },
    { value: 'week', label: 'Última Semana' },
    { value: 'month', label: 'Último Mes' },
    { value: 'quarter', label: 'Último Trimestre' },
    { value: 'year', label: 'Último Año' },
    { value: 'all_time', label: 'Todo el Tiempo' }
  ];

  const handleChange = (newPreset) => {
    setPreset(newPreset);
    onChange(newPreset);
  };

  return (
    <div className="date-selector">
      {presets.map(p => (
        <button
          key={p.value}
          className={preset === p.value ? 'active' : ''}
          onClick={() => handleChange(p.value)}
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}
```

---

## Soporte

Para preguntas o problemas con la API, contacta al equipo de desarrollo.

**Versión del documento**: 1.0
**Última actualización**: Noviembre 2025
