import re
import uuid
from typing import Optional, Union
from datetime import datetime, timedelta
import qrcode
import io
import base64
from pathlib import Path
import os

# Función para validar emails
def is_valid_email(email: str) -> bool:
    """
    Valida si un string es un email válido
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

# Función para generar un UUID
def generate_uuid() -> uuid.UUID:
    """
    Genera y retorna un UUID v4
    """
    return uuid.uuid4()

# Función para generar un token de expiración
def generate_expiration_date(hours: int) -> datetime:
    """
    Genera una fecha de expiración basada en horas a partir de ahora
    """
    return datetime.utcnow() + timedelta(hours=hours)

# Función para generar un QR code
def generate_qr_code(data: Union[str, dict]) -> str:
    """
    Genera un código QR como imagen base64 a partir de datos
    """
    if isinstance(data, dict):
        import json
        data = json.dumps(data)
        
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    return f"data:image/png;base64,{qr_base64}"

# Función para guardar un archivo
def save_upload_file(upload_file, directory: Union[str, Path]) -> str:
    """
    Guarda un archivo subido y retorna la ruta relativa
    """
    directory_path = Path(directory)
    directory_path.mkdir(parents=True, exist_ok=True)
    
    # Generar nombre único para el archivo
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{generate_uuid()}{file_extension}"
    file_path = directory_path / unique_filename
    
    # Guardar el archivo
    with open(file_path, "wb") as f:
        f.write(upload_file.file.read())
    
    return str(file_path)

# Función para truncar texto en la salida
def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Trunca un texto si excede el máximo de caracteres
    """
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."