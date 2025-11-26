# API Documentation - Nuevas Funcionalidades

Esta documentación detalla los endpoints implementados para las nuevas funcionalidades de la plataforma de gestión de activos.

## Tabla de Contenidos

1. [Gestión de Imágenes de Activos](#gestión-de-imágenes-de-activos)
2. [Generación y Obtención de Códigos QR](#generación-y-obtención-de-códigos-qr)
3. [Operaciones en Lote de Activos](#operaciones-en-lote-de-activos)
4. [Inventario de Aula](#inventario-de-aula)

---

## Gestión de Imágenes de Activos

### Actualizar Imagen de un Activo

Permite actualizar la URL de la imagen de un activo específico sin modificar otras propiedades.

**Endpoint:** `PATCH /assets/{asset_id}/image`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Path Parameters:**
- `asset_id` (UUID): ID del activo a actualizar

**Request Body:**
```json
{
  "image_url": "https://ejemplo.com/imagen.jpg"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid-del-activo",
  "template_id": "uuid-del-template",
  "serial_number": "SN-12345",
  "purchase_date": "2024-01-15",
  "value_estimate": 81000,
  "image_url": "https://ejemplo.com/imagen.jpg",
  "status": "available",
  "classroom_id": "uuid-del-aula",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z",
  "template": { ... },
  "qr_code": { ... }
}
```

**Ejemplo Frontend (JavaScript/React):**
```javascript
const updateAssetImage = async (assetId, imageUrl) => {
  try {
    const response = await fetch(`${API_BASE_URL}/assets/${assetId}/image`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ image_url: imageUrl })
    });

    if (!response.ok) throw new Error('Error al actualizar imagen');

    const updatedAsset = await response.json();
    console.log('Imagen actualizada:', updatedAsset);
    return updatedAsset;
  } catch (error) {
    console.error('Error:', error);
  }
};

// Uso
await updateAssetImage('asset-uuid', 'https://nueva-imagen.jpg');
```

---

## Generación y Obtención de Códigos QR

### Generar o Regenerar QR de un Activo

Permite generar un código QR para un activo o regenerarlo si ya existe. Esto permite imprimir el QR en cualquier momento, incluso si se salió de la pantalla inicial.

**Endpoint:** `POST /assets/{asset_id}/qr-codes/`

**Headers:**
```
Authorization: Bearer {token}
```

**Path Parameters:**
- `asset_id` (UUID): ID del activo

**Response:** `201 Created` o `200 OK`
```json
{
  "id": "uuid-del-qr",
  "asset_id": "uuid-del-activo",
  "qr_url": "data:image/png;base64,iVBORw0KGgoAAAANSUh...",
  "payload": {
    "asset_id": "uuid-del-activo",
    "asset_url": "https://issa-qr.vercel.app/assets/uuid-del-activo"
  }
}
```

**Ejemplo Frontend:**
```javascript
const generateQRCode = async (assetId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/assets/${assetId}/qr-codes/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) throw new Error('Error al generar QR');

    const qrData = await response.json();

    // Mostrar QR en un elemento img
    const imgElement = document.getElementById('qr-display');
    imgElement.src = qrData.qr_url;

    // O descargar directamente
    const link = document.createElement('a');
    link.href = qrData.qr_url;
    link.download = `QR-${assetId}.png`;
    link.click();

    return qrData;
  } catch (error) {
    console.error('Error:', error);
  }
};

// Uso
await generateQRCode('asset-uuid');
```

### Obtener QR Existente de un Activo

Obtiene el código QR existente de un activo sin regenerarlo.

**Endpoint:** `GET /assets/{asset_id}/qr-codes/`

**Headers:**
```
Authorization: Bearer {token}
```

**Path Parameters:**
- `asset_id` (UUID): ID del activo

**Response:** `200 OK`
```json
{
  "id": "uuid-del-qr",
  "asset_id": "uuid-del-activo",
  "qr_url": "data:image/png;base64,iVBORw0KGgoAAAANSUh...",
  "payload": {
    "asset_id": "uuid-del-activo",
    "asset_url": "https://issa-qr.vercel.app/assets/uuid-del-activo"
  }
}
```

**Ejemplo Frontend:**
```javascript
const getExistingQR = async (assetId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/assets/${assetId}/qr-codes/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      if (response.status === 404) {
        // QR no existe, generarlo
        return await generateQRCode(assetId);
      }
      throw new Error('Error al obtener QR');
    }

    const qrData = await response.json();
    return qrData;
  } catch (error) {
    console.error('Error:', error);
  }
};
```

---

## Operaciones en Lote de Activos

### Eliminar Múltiples Activos

Permite eliminar varios activos a la vez, útil cuando se crearon múltiples activos del mismo tipo y se desea eliminar una cantidad específica.

**Endpoint:** `POST /assets/bulk-delete`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "asset_ids": [
    "uuid-activo-1",
    "uuid-activo-2",
    "uuid-activo-3"
  ]
}
```

**Response:** `200 OK`
```json
{
  "deleted_count": 3,
  "total_requested": 3,
  "errors": null
}
```

**Response con Errores:**
```json
{
  "deleted_count": 2,
  "total_requested": 3,
  "errors": [
    {
      "asset_id": "uuid-activo-3",
      "error": "Asset not found or already deleted"
    }
  ]
}
```

**Ejemplo Frontend:**
```javascript
const bulkDeleteAssets = async (assetIds) => {
  try {
    const response = await fetch(`${API_BASE_URL}/assets/bulk-delete`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ asset_ids: assetIds })
    });

    if (!response.ok) throw new Error('Error al eliminar activos');

    const result = await response.json();
    console.log(`Eliminados: ${result.deleted_count}/${result.total_requested}`);

    if (result.errors) {
      console.warn('Algunos activos no se pudieron eliminar:', result.errors);
    }

    return result;
  } catch (error) {
    console.error('Error:', error);
  }
};

// Uso: Eliminar 5 sillas de las 10 creadas
const selectedAssetIds = ['uuid-1', 'uuid-2', 'uuid-3', 'uuid-4', 'uuid-5'];
await bulkDeleteAssets(selectedAssetIds);
```

### Actualizar Múltiples Activos

Permite actualizar propiedades de múltiples activos a la vez, útil para modificar el valor, estado o imagen de varios activos del mismo tipo.

**Endpoint:** `PATCH /assets/bulk-update`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "asset_ids": [
    "uuid-activo-1",
    "uuid-activo-2"
  ],
  "value_estimate": 90000,
  "status": "available",
  "image_url": "https://ejemplo.com/nueva-imagen.jpg"
}
```

**Nota:** Todos los campos son opcionales excepto `asset_ids`. Solo incluye los campos que deseas actualizar.

**Response:** `200 OK`
```json
{
  "updated_count": 2,
  "total_requested": 2,
  "errors": null
}
```

**Ejemplo Frontend:**
```javascript
const bulkUpdateAssets = async (assetIds, updates) => {
  try {
    const response = await fetch(`${API_BASE_URL}/assets/bulk-update`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        asset_ids: assetIds,
        ...updates
      })
    });

    if (!response.ok) throw new Error('Error al actualizar activos');

    const result = await response.json();
    console.log(`Actualizados: ${result.updated_count}/${result.total_requested}`);

    if (result.errors) {
      console.warn('Algunos activos no se pudieron actualizar:', result.errors);
    }

    return result;
  } catch (error) {
    console.error('Error:', error);
  }
};

// Uso: Actualizar el valor de 10 sillas
const chairIds = ['uuid-1', 'uuid-2', /* ... */ 'uuid-10'];
await bulkUpdateAssets(chairIds, { value_estimate: 85000 });

// Actualizar estado de varios activos
await bulkUpdateAssets(chairIds, { status: 'in_repair' });
```

---

## Inventario de Aula

### Obtener Inventario Completo de un Aula

Obtiene un resumen detallado de todos los activos en un aula, agrupados por tipo/template. Muestra la cantidad de cada tipo de activo, su valor individual, valor total, categoría y estado.

**Endpoint:** `GET /classrooms/{classroom_id}/inventory`

**Headers:**
```
Authorization: Bearer {token}
```

**Path Parameters:**
- `classroom_id` (UUID): ID del aula

**Response:** `200 OK`
```json
{
  "classroom_id": "uuid-del-aula",
  "classroom_name": "SUM Santa Mónica",
  "classroom_code": "SUM-SM-01",
  "school_id": "uuid-de-la-escuela",
  "total_assets": 12,
  "total_value": 910000,
  "assets": [
    {
      "template_name": "Silla naranja con pupitre",
      "category_name": "Mobiliarios y equipos",
      "status": "available",
      "value_estimate": 81000,
      "quantity": 10,
      "total_value": 810000,
      "asset_ids": [
        "uuid-activo-1",
        "uuid-activo-2",
        "...",
        "uuid-activo-10"
      ]
    },
    {
      "template_name": "Mesa",
      "category_name": "Mobiliarios y equipos",
      "status": "available",
      "value_estimate": 50000,
      "quantity": 2,
      "total_value": 100000,
      "asset_ids": [
        "uuid-activo-11",
        "uuid-activo-12"
      ]
    }
  ]
}
```

**Ejemplo Frontend (React):**
```javascript
const ClassroomInventory = ({ classroomId }) => {
  const [inventory, setInventory] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInventory = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/classrooms/${classroomId}/inventory`,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );

        if (!response.ok) throw new Error('Error al cargar inventario');

        const data = await response.json();
        setInventory(data);
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchInventory();
  }, [classroomId]);

  if (loading) return <div>Cargando...</div>;
  if (!inventory) return <div>Error al cargar inventario</div>;

  return (
    <div>
      <h1>{inventory.classroom_name}</h1>
      <p>Código: {inventory.classroom_code}</p>
      <p>Total de activos: {inventory.total_assets}</p>
      <p>Valor total: ${inventory.total_value.toLocaleString()}</p>

      <table>
        <thead>
          <tr>
            <th>Activo</th>
            <th>Categoría</th>
            <th>Estado</th>
            <th>Valor</th>
            <th>Cantidad</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          {inventory.assets.map((asset, index) => (
            <tr key={index}>
              <td>{asset.template_name}</td>
              <td>{asset.category_name || 'N/A'}</td>
              <td>{asset.status}</td>
              <td>${asset.value_estimate?.toLocaleString() || 'N/A'}</td>
              <td>{asset.quantity}</td>
              <td>${asset.total_value?.toLocaleString() || 'N/A'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

**Ejemplo Vanilla JavaScript:**
```javascript
const displayClassroomInventory = async (classroomId) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/classrooms/${classroomId}/inventory`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );

    if (!response.ok) throw new Error('Error al cargar inventario');

    const inventory = await response.json();

    // Crear tabla HTML
    let html = `
      <h2>${inventory.classroom_name}</h2>
      <p>Total activos: ${inventory.total_assets} | Valor total: $${inventory.total_value.toLocaleString()}</p>
      <table border="1">
        <thead>
          <tr>
            <th>Activo</th>
            <th>Categoría</th>
            <th>Estado</th>
            <th>Valor</th>
            <th>Cantidad</th>
          </tr>
        </thead>
        <tbody>
    `;

    inventory.assets.forEach(asset => {
      html += `
        <tr>
          <td>${asset.template_name}</td>
          <td>${asset.category_name || 'N/A'}</td>
          <td>${asset.status}</td>
          <td>$${asset.value_estimate?.toLocaleString() || 'N/A'}</td>
          <td>${asset.quantity}</td>
        </tr>
      `;
    });

    html += '</tbody></table>';

    document.getElementById('inventory-container').innerHTML = html;

    return inventory;
  } catch (error) {
    console.error('Error:', error);
  }
};

// Uso
await displayClassroomInventory('classroom-uuid');
```

---

## Casos de Uso Completos

### Caso 1: Gestión de Imágenes desde Galería

```javascript
// 1. Usuario selecciona imagen desde galería o cámara
const handleImageSelect = async (file, assetId) => {
  // Subir imagen a servicio de almacenamiento (ej: Cloudinary, S3)
  const formData = new FormData();
  formData.append('file', file);

  const uploadResponse = await fetch('https://api.cloudinary.com/v1_1/YOUR_CLOUD/upload', {
    method: 'POST',
    body: formData
  });

  const { secure_url } = await uploadResponse.json();

  // 2. Actualizar activo con nueva imagen
  await updateAssetImage(assetId, secure_url);

  console.log('Imagen actualizada exitosamente');
};
```

### Caso 2: Imprimir QR después de crear activos

```javascript
// Usuario creó 10 sillas, se salió de la pantalla, y ahora quiere imprimir los QR
const printQRCodesForAssets = async (assetIds) => {
  for (const assetId of assetIds) {
    // Regenerar o obtener QR
    const qrData = await generateQRCode(assetId);

    // Crear imagen y agregarla a un contenedor para imprimir
    const img = document.createElement('img');
    img.src = qrData.qr_url;
    img.style.width = '200px';
    img.style.margin = '10px';

    document.getElementById('print-container').appendChild(img);
  }

  // Imprimir
  window.print();
};
```

### Caso 3: Editar valor de múltiples activos del mismo tipo

```javascript
// Usuario creó 10 sillas con valor $81.000 pero quiere cambiarlas a $85.000
const updateChairPrices = async () => {
  // 1. Obtener todos los activos del aula
  const response = await fetch(`${API_BASE_URL}/classrooms/${classroomId}/inventory`);
  const inventory = await response.json();

  // 2. Encontrar el grupo de sillas
  const chairGroup = inventory.assets.find(
    asset => asset.template_name === 'Silla naranja con pupitre'
  );

  if (chairGroup) {
    // 3. Actualizar todas las sillas
    await bulkUpdateAssets(chairGroup.asset_ids, { value_estimate: 85000 });
    console.log(`${chairGroup.quantity} sillas actualizadas`);
  }
};
```

### Caso 4: Eliminar solo 3 de 10 sillas creadas

```javascript
// Usuario creó 10 sillas pero solo necesita 7
const deleteExtraChairs = async (allChairIds) => {
  // Seleccionar solo 3 para eliminar
  const chairsToDelete = allChairIds.slice(0, 3);

  const result = await bulkDeleteAssets(chairsToDelete);

  console.log(`Eliminadas ${result.deleted_count} sillas. Quedan 7.`);
};
```

---

## Notas Importantes

### Autenticación

Todos los endpoints requieren autenticación mediante JWT token en el header `Authorization: Bearer {token}`. Asegúrate de incluir el token en todas las peticiones.

### Manejo de Errores

Todos los endpoints pueden retornar los siguientes códigos de error:

- `400 Bad Request`: Datos de entrada inválidos
- `401 Unauthorized`: Token de autenticación inválido o ausente
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor

**Ejemplo de manejo de errores:**
```javascript
const handleAPICall = async (url, options) => {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error en la petición');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error.message);
    // Mostrar mensaje al usuario
    alert(`Error: ${error.message}`);
    return null;
  }
};
```

### Estados de Activos

Los estados disponibles para activos son:
- `available`: Disponible
- `in_repair`: En reparación
- `missing`: Extraviado
- `decommissioned`: Dado de baja
- `operational`: Operacional

### Base URL

Reemplaza `${API_BASE_URL}` con la URL base de tu API:
- Desarrollo: `http://localhost:8000` o `http://localhost:3000`
- Producción: `https://tu-api.com`

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

---

## Resumen de Endpoints

| Funcionalidad | Método | Endpoint |
|--------------|--------|----------|
| Actualizar imagen de activo | PATCH | `/assets/{asset_id}/image` |
| Generar/Regenerar QR | POST | `/assets/{asset_id}/qr-codes/` |
| Obtener QR existente | GET | `/assets/{asset_id}/qr-codes/` |
| Eliminar múltiples activos | POST | `/assets/bulk-delete` |
| Actualizar múltiples activos | PATCH | `/assets/bulk-update` |
| Obtener inventario de aula | GET | `/classrooms/{classroom_id}/inventory` |

---

## Soporte

Para más información o problemas, contacta al equipo de desarrollo o revisa la documentación de Swagger en `/docs` de la API.
