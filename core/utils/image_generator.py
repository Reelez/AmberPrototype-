import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import inch
from reportlab.lib.units import cm
from reportlab.lib import colors
from pdf2image import convert_from_path
from django.conf import settings


def generate_alert_pdf(alerta, pdf_path):
    """
    Genera un PDF cuadrado (para redes) con colores de Panamá.
    """
    # Tamaño cuadrado: 20x20 cm
    width = height = 20 * cm

    c = canvas.Canvas(pdf_path, pagesize=(width, height))

    # Fondo
    c.setFillColor(colors.whitesmoke)
    c.rect(0, 0, width, height, fill=1)

    # Header: Amber Panama Prototype
    c.setFillColor(colors.red)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 2 * cm, "AMBER PANAMA PROTOTYPE")

    # Datos principales
    c.setFillColor(colors.darkblue)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1.5 * cm, height - 4 * cm, "Datos del menor:")

    c.setFont("Helvetica", 14)
    c.drawString(1.5 * cm, height - 5 * cm, f"👤 Nombre: {alerta.nombre_desaparecido}")
    c.drawString(1.5 * cm, height - 6 * cm, f"🎂 Edad: {alerta.edad} años")
    c.drawString(1.5 * cm, height - 7 * cm, f"📍 Última ubicación: {alerta.ultima_ubicacion}")
    c.drawString(1.5 * cm, height - 8 * cm, f"📅 Fecha desaparición: {alerta.fecha_desaparicion}")
    c.drawString(1.5 * cm, height - 9 * cm, f"⏰ Hora desaparición: {alerta.hora_desaparicion.strftime('%H:%M')}")

    # Foto del menor
    if alerta.imagen and os.path.exists(alerta.imagen.path):
        img_path = alerta.imagen.path
        c.drawImage(img_path, width - 9 * cm, height - 12 * cm, width=7 * cm, height=7 * cm, preserveAspectRatio=True, mask='auto')
    else:
        # Placeholder si no hay foto
        c.setFillColor(colors.lightgrey)
        c.rect(width - 9 * cm, height - 12 * cm, 7 * cm, 7 * cm, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawCentredString(width - 5.5 * cm, height - 8.5 * cm, "Sin foto")

    # Footer: texto oficial
    c.setFillColor(colors.red)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2, 1.2 * cm,
                        "Cumpliendo con los parámetros establecidos en la Ley 469 del 08 de mayo de 2025.")
    c.drawCentredString(width / 2, 0.7 * cm,
                        "PRUEBA DE PROTOTIPO AMBER – INFORMACIÓN NO OFICIAL, SOLO ES UN PROTOTIPO.")

    c.save()


def convert_pdf_to_png(pdf_path, png_path):
    """
    Convierte el PDF a PNG para publicación en redes.
    """
    images = convert_from_path(pdf_path, dpi=300)
    if images:
        images[0].save(png_path, 'PNG')


def generate_alert_image(alerta):
    """
    Genera el PDF y luego lo convierte en PNG.
    """
    folder = os.path.join(settings.MEDIA_ROOT, "alertas_generadas")
    os.makedirs(folder, exist_ok=True)

    pdf_path = os.path.join(folder, f"alerta_{alerta.id}.pdf")
    png_path = os.path.join(folder, f"alerta_{alerta.id}.png")

    # 1️⃣ Generar PDF
    generate_alert_pdf(alerta, pdf_path)

    # 2️⃣ Convertir a PNG
    convert_pdf_to_png(pdf_path, png_path)

    return png_path
