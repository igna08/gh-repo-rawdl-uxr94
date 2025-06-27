import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


def send_invitation_email(recipient_email: str, invitation_token: str):
    """
    Envía un correo de invitación al usuario invitado, usando Gmail (SMTP SSL).
    El mensaje contiene un botón que redirige al frontend con el token en la URL.
    """
    sender_email = settings.SMTP_SENDER_EMAIL
    smtp_server = settings.SMTP_SERVER
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER
    smtp_password = settings.SMTP_PASSWORD

    subject = "Invitación a Scanly - Sistema de Gestión Educativa"
    # La URL de tu frontend que recibirá el token como query param
    link = f"{settings.FRONTEND_URL}/register/invitation?token={invitation_token}"

    # HTML del correo con diseño moderno inspirado en el sidebar
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Invitación a Scanly</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        </style>
    </head>
    <body style="
        margin: 0; 
        padding: 0; 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
        background-color: #f8fafc; 
        color: #1f2937;
        line-height: 1.6;
    ">
        <!-- Container principal -->
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 40px 20px;">
                    <!-- Tarjeta principal -->
                    <table role="presentation" style="
                        max-width: 600px; 
                        margin: 0 auto; 
                        background-color: #ffffff; 
                        border-radius: 16px; 
                        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                        border: 1px solid #e5e7eb;
                        overflow: hidden;
                    ">
                        <!-- Header con logo -->
                        <tr>
                            <td style="
                                background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                                padding: 40px 40px 30px;
                                text-align: center;
                            ">
                                <!-- Logo -->
                                <img src="https://app-web-final-qr.vercel.app/logo.png" 
                                    alt="Scanly Logo" 
                                    style="
                                        height: 70px; 
                                        width: auto; 
                                        max-width: 180px;
                                        margin-bottom: 20px;
                                        filter: brightness(0) invert(1);
                                        display: block;
                                        margin-left: auto;
                                        margin-right: auto;
                                    "
                                />
                                <h1 style="
                                    color: #ffffff; 
                                    font-size: 28px; 
                                    font-weight: 700; 
                                    margin: 0;
                                    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                ">
                                    ¡Has sido invitado!
                                </h1>
                            </td>
                        </tr>
                        
                        <!-- Contenido principal -->
                        <tr>
                            <td style="padding: 40px;">
                                <!-- Saludo -->
                                <div style="
                                    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                                    border-left: 4px solid #3b82f6;
                                    padding: 20px;
                                    border-radius: 8px;
                                    margin-bottom: 30px;
                                ">
                                    <h2 style="
                                        color: #1e40af; 
                                        font-size: 20px; 
                                        font-weight: 600; 
                                        margin: 0 0 10px 0;
                                    ">
                                        ¡Bienvenido a Scanly!
                                    </h2>
                                    <p style="
                                        color: #1f2937; 
                                        font-size: 16px; 
                                        margin: 0;
                                        font-weight: 500;
                                    ">
                                        Sistema de Gestión Educativa
                                    </p>
                                </div>

                                <!-- Mensaje principal -->
                                <p style="
                                    font-size: 16px; 
                                    color: #374151; 
                                    margin: 0 0 25px 0;
                                    line-height: 1.7;
                                ">
                                    Has sido invitado a formar parte de nuestra plataforma de gestión educativa. 
                                    Scanly te permitirá administrar activos, escuelas, usuarios y mucho más de manera eficiente.
                                </p>

                                <p style="
                                    font-size: 16px; 
                                    color: #374151; 
                                    margin: 0 0 35px 0;
                                    line-height: 1.7;
                                ">
                                    Para completar tu registro y acceder a todas las funcionalidades, 
                                    haz clic en el botón de abajo:
                                </p>

                                <!-- Botón CTA -->
                                <div style="text-align: center; margin: 40px 0;">
                                    <a 
                                        href="{link}" 
                                        style="
                                            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                                            color: #ffffff;
                                            padding: 16px 32px;
                                            text-decoration: none;
                                            border-radius: 12px;
                                            display: inline-block;
                                            font-size: 16px;
                                            font-weight: 600;
                                            box-shadow: 0 4px 14px 0 rgba(59, 130, 246, 0.4);
                                            transition: all 0.2s ease;
                                            text-transform: uppercase;
                                            letter-spacing: 0.5px;
                                        "
                                        target="_blank"
                                    >
                                        ✨ Aceptar Invitación
                                    </a>
                                </div>

                                <!-- Características destacadas -->
                                <div style="
                                    background-color: #f9fafb;
                                    border-radius: 12px;
                                    padding: 25px;
                                    margin: 35px 0;
                                    border: 1px solid #e5e7eb;
                                ">
                                    <h3 style="
                                        color: #1f2937;
                                        font-size: 18px;
                                        font-weight: 600;
                                        margin: 0 0 20px 0;
                                        text-align: center;
                                    ">
                                        🚀 Lo que podrás hacer con Scanly:
                                    </h3>
                                    <table role="presentation" style="width: 100%;">
                                        <tr>
                                            <td style="width: 50%; padding: 8px 12px;">
                                                <div style="display: flex; align-items: center;">
                                                    <span style="color: #10b981; font-size: 18px; margin-right: 8px;">🏫</span>
                                                    <span style="color: #374151; font-size: 14px; font-weight: 500;">Gestionar Escuelas</span>
                                                </div>
                                            </td>
                                            <td style="width: 50%; padding: 8px 12px;">
                                                <div style="display: flex; align-items: center;">
                                                    <span style="color: #10b981; font-size: 18px; margin-right: 8px;">💻</span>
                                                    <span style="color: #374151; font-size: 14px; font-weight: 500;">Administrar Activos</span>
                                                </div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="width: 50%; padding: 8px 12px;">
                                                <div style="display: flex; align-items: center;">
                                                    <span style="color: #10b981; font-size: 18px; margin-right: 8px;">👥</span>
                                                    <span style="color: #374151; font-size: 14px; font-weight: 500;">Controlar Usuarios</span>
                                                </div>
                                            </td>
                                            <td style="width: 50%; padding: 8px 12px;">
                                                <div style="display: flex; align-items: center;">
                                                    <span style="color: #10b981; font-size: 18px; margin-right: 8px;">📊</span>
                                                    <span style="color: #374151; font-size: 14px; font-weight: 500;">Generar Reportes</span>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                </div>

                                <!-- Link alternativo -->
                                <div style="
                                    background-color: #fef3c7;
                                    border: 1px solid #f59e0b;
                                    border-radius: 8px;
                                    padding: 16px;
                                    margin: 30px 0;
                                ">
                                    <p style="
                                        font-size: 14px; 
                                        color: #92400e; 
                                        margin: 0 0 8px 0;
                                        font-weight: 600;
                                    ">
                                        ⚠️ ¿El botón no funciona?
                                    </p>
                                    <p style="
                                        font-size: 14px; 
                                        color: #92400e; 
                                        margin: 0;
                                    ">
                                        Copia y pega este enlace en tu navegador:
                                    </p>
                                    <p style="
                                        word-break: break-all; 
                                        font-size: 12px; 
                                        color: #1d4ed8; 
                                        background-color: #ffffff; 
                                        padding: 8px; 
                                        border-radius: 4px; 
                                        margin: 8px 0 0 0;
                                        font-family: 'Courier New', monospace;
                                    ">
                                        <a href="{link}" style="color: #1d4ed8; text-decoration: none;" target="_blank">{link}</a>
                                    </p>
                                </div>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="
                                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                                padding: 30px 40px;
                                border-top: 1px solid #e5e7eb;
                                text-align: center;
                            ">
                                <div style="
                                    background-color: #ffffff;
                                    border: 1px solid #e5e7eb;
                                    border-radius: 8px;
                                    padding: 20px;
                                    margin-bottom: 20px;
                                ">
                                    <p style="
                                        font-size: 14px; 
                                        color: #6b7280; 
                                        margin: 0 0 8px 0;
                                        font-weight: 600;
                                    ">
                                        ⏰ Información importante:
                                    </p>
                                    <p style="
                                        font-size: 13px; 
                                        color: #6b7280; 
                                        margin: 0;
                                        line-height: 1.5;
                                    ">
                                        Este enlace de invitación expirará pronto por motivos de seguridad.<br>
                                        Si no solicitaste esta invitación, puedes ignorar este correo de forma segura.
                                    </p>
                                </div>
                                
                                <p style="
                                    font-size: 12px; 
                                    color: #9ca3af; 
                                    margin: 0;
                                    font-style: italic;
                                ">
                                    © 2025 Scanly - Sistema de Gestión Educativa
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    # Construimos el mensaje MIME
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        # Aquí podrías loguear con el logger que uses en tu proyecto
        print(f"Error al enviar correo de invitación: {e}")
        raise