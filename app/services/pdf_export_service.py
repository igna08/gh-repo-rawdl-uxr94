from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class PDFReportGenerator:
    """Generator for PDF reports with professional formatting"""

    def __init__(self, pagesize=A4):
        self.pagesize = pagesize
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))

        # Info text style
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_RIGHT
        ))

    def _create_header(self, title: str, date_range: Dict[str, Any]) -> List:
        """Create PDF header with title and date range"""
        elements = []

        # Title
        title_para = Paragraph(title, self.styles['CustomTitle'])
        elements.append(title_para)
        elements.append(Spacer(1, 0.2 * inch))

        # Date range info
        date_info = self._format_date_range(date_range)
        date_para = Paragraph(date_info, self.styles['InfoText'])
        elements.append(date_para)

        # Generated timestamp
        generated_text = f"Generado: {datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}"
        generated_para = Paragraph(generated_text, self.styles['InfoText'])
        elements.append(generated_para)

        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _format_date_range(self, date_range: Dict[str, Any]) -> str:
        """Format date range for display"""
        if date_range.get('preset'):
            preset_names = {
                'today': 'Hoy',
                'week': 'Última Semana',
                'month': 'Último Mes',
                'quarter': 'Último Trimestre',
                'year': 'Último Año',
                'all_time': 'Todo el Tiempo'
            }
            return f"<b>Período:</b> {preset_names.get(date_range['preset'], date_range['preset'])}"

        start = date_range.get('start')
        end = date_range.get('end')

        if start and end:
            start_str = datetime.fromisoformat(str(start).replace('Z', '+00:00')).strftime('%d/%m/%Y')
            end_str = datetime.fromisoformat(str(end).replace('Z', '+00:00')).strftime('%d/%m/%Y')
            return f"<b>Período:</b> {start_str} - {end_str}"

        return "<b>Período:</b> Todos los datos"

    def _create_summary_table(self, data: List[List[str]], title: str = None) -> List:
        """Create a formatted table with optional title"""
        elements = []

        if title:
            elements.append(Paragraph(title, self.styles['SectionHeader']))
            elements.append(Spacer(1, 0.1 * inch))

        # Create table
        table = Table(data, hAlign='LEFT')

        # Style the table
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),

            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#3b82f6')),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_key_metrics(self, metrics: Dict[str, Any]) -> List:
        """Create key metrics summary boxes"""
        elements = []

        # Create metrics table
        data = [[Paragraph('<b>Métrica</b>', self.styles['Normal']),
                 Paragraph('<b>Valor</b>', self.styles['Normal'])]]

        for key, value in metrics.items():
            data.append([
                Paragraph(key, self.styles['Normal']),
                Paragraph(f'<b>{value}</b>', self.styles['Normal'])
            ])

        elements.extend(self._create_summary_table(data, "📊 Resumen Ejecutivo"))

        return elements

    # ========================================================================
    # Asset Report PDF
    # ========================================================================

    def generate_asset_report_pdf(self, report_data: Dict[str, Any]) -> BytesIO:
        """Generate PDF for asset report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.pagesize,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)

        elements = []

        # Header
        elements.extend(self._create_header(
            "Reporte de Activos",
            report_data.get('date_range', {})
        ))

        # Key Metrics
        metrics = {
            'Total de Activos': f"{report_data.get('total_assets', 0):,}",
            'Valor Total del Inventario': f"${report_data.get('total_value', 0):,.2f}",
            'Activos sin Template': f"{report_data.get('assets_without_template', 0)}"
        }
        elements.extend(self._create_key_metrics(metrics))

        # Assets by Status
        if report_data.get('by_status'):
            status_data = [['Estado', 'Cantidad', 'Valor Total']]
            status_names = {
                'available': 'Disponible',
                'in_use': 'En Uso',
                'maintenance': 'Mantenimiento',
                'retired': 'Retirado',
                'decommissioned': 'Dado de Baja'
            }

            for item in report_data['by_status']:
                status_data.append([
                    status_names.get(item['status'], item['status']),
                    f"{item['count']:,}",
                    f"${item['total_value']:,.2f}"
                ])

            elements.extend(self._create_summary_table(status_data, "📦 Distribución por Estado"))

        # Assets by Category
        if report_data.get('by_category'):
            category_data = [['Categoría', 'Cantidad', 'Valor Total']]

            for item in report_data['by_category']:
                category_data.append([
                    item['category_name'],
                    f"{item['count']:,}",
                    f"${item['total_value']:,.2f}"
                ])

            elements.extend(self._create_summary_table(category_data, "🏷️ Distribución por Categoría"))

        # Assets by School
        if report_data.get('by_school'):
            school_data = [['Escuela', 'Cantidad', 'Valor Total']]

            for item in report_data['by_school']:
                school_data.append([
                    item['school_name'],
                    f"{item['count']:,}",
                    f"${item['total_value']:,.2f}"
                ])

            elements.extend(self._create_summary_table(school_data, "🏫 Distribución por Escuela"))

        # Top Valued Assets
        if report_data.get('top_valued_assets'):
            top_assets_data = [['Nombre', 'Serie', 'Estado', 'Valor']]

            for asset in report_data['top_valued_assets'][:10]:
                top_assets_data.append([
                    asset.get('template_name', 'Sin nombre')[:30],
                    asset.get('serial_number', 'N/A')[:15],
                    asset.get('status', 'N/A'),
                    f"${asset.get('value_estimate', 0):,.2f}"
                ])

            elements.extend(self._create_summary_table(top_assets_data, "💎 Top 10 Activos Más Valiosos"))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    # ========================================================================
    # Incident Report PDF
    # ========================================================================

    def generate_incident_report_pdf(self, report_data: Dict[str, Any]) -> BytesIO:
        """Generate PDF for incident report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.pagesize,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)

        elements = []

        # Header
        elements.extend(self._create_header(
            "Reporte de Incidentes",
            report_data.get('date_range', {})
        ))

        # Key Metrics
        avg_resolution = report_data.get('average_resolution_hours')
        avg_text = f"{avg_resolution:.1f} horas" if avg_resolution else "N/A"

        metrics = {
            'Total de Incidentes': f"{report_data.get('total_incidents', 0):,}",
            'Incidentes Sin Resolver': f"{report_data.get('unresolved_count', 0):,}",
            'Tiempo Promedio de Resolución': avg_text
        }
        elements.extend(self._create_key_metrics(metrics))

        # Incidents by Status
        if report_data.get('by_status'):
            status_data = [['Estado', 'Cantidad']]
            status_names = {
                'open': 'Abierto',
                'in_progress': 'En Progreso',
                'resolved': 'Resuelto',
                'closed': 'Cerrado'
            }

            for item in report_data['by_status']:
                status_data.append([
                    status_names.get(item['status'], item['status']),
                    f"{item['count']:,}"
                ])

            elements.extend(self._create_summary_table(status_data, "⚠️ Distribución por Estado"))

        # Top Assets with Incidents
        if report_data.get('top_assets_with_incidents'):
            top_assets_data = [['Activo', 'Serie', 'Cantidad de Incidentes']]

            for item in report_data['top_assets_with_incidents'][:10]:
                top_assets_data.append([
                    item.get('template_name', 'Sin nombre')[:40],
                    item.get('serial_number', 'N/A')[:15],
                    f"{item['incident_count']:,}"
                ])

            elements.extend(self._create_summary_table(top_assets_data, "🔧 Activos con Más Incidentes"))

        # Recent Incidents
        if report_data.get('recent_incidents'):
            recent_data = [['Descripción', 'Estado', 'Reportado']]

            for incident in report_data['recent_incidents'][:15]:
                reported_at = incident.get('reported_at')
                if reported_at:
                    reported_str = datetime.fromisoformat(str(reported_at).replace('Z', '+00:00')).strftime('%d/%m/%Y')
                else:
                    reported_str = 'N/A'

                status_names = {
                    'open': 'Abierto',
                    'in_progress': 'En Progreso',
                    'resolved': 'Resuelto',
                    'closed': 'Cerrado'
                }

                recent_data.append([
                    incident.get('description', '')[:50],
                    status_names.get(incident.get('status'), incident.get('status')),
                    reported_str
                ])

            elements.extend(self._create_summary_table(recent_data, "📋 Incidentes Recientes"))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    # ========================================================================
    # Overview Report PDF
    # ========================================================================

    def generate_overview_report_pdf(self, report_data: Dict[str, Any]) -> BytesIO:
        """Generate comprehensive overview PDF combining assets and incidents"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.pagesize,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)

        elements = []

        # Header
        assets_data = report_data.get('assets', {})
        elements.extend(self._create_header(
            "Reporte General del Sistema",
            assets_data.get('date_range', {})
        ))

        # ========== ASSETS SECTION ==========
        elements.append(Paragraph("SECCIÓN: ACTIVOS", self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.1 * inch))

        # Assets Key Metrics
        metrics = {
            'Total de Activos': f"{assets_data.get('total_assets', 0):,}",
            'Valor Total del Inventario': f"${assets_data.get('total_value', 0):,.2f}",
            'Activos sin Template': f"{assets_data.get('assets_without_template', 0)}"
        }
        elements.extend(self._create_key_metrics(metrics))

        # Assets by Status (compact)
        if assets_data.get('by_status'):
            status_data = [['Estado', 'Cantidad', 'Valor']]
            status_names = {
                'available': 'Disponible',
                'in_use': 'En Uso',
                'maintenance': 'Mantenimiento',
                'retired': 'Retirado',
                'decommissioned': 'Dado de Baja'
            }

            for item in assets_data['by_status']:
                status_data.append([
                    status_names.get(item['status'], item['status']),
                    f"{item['count']:,}",
                    f"${item['total_value']:,.2f}"
                ])

            elements.extend(self._create_summary_table(status_data, "Activos por Estado"))

        # Page break before incidents
        elements.append(PageBreak())

        # ========== INCIDENTS SECTION ==========
        incidents_data = report_data.get('incidents', {})
        elements.append(Paragraph("SECCIÓN: INCIDENTES", self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.1 * inch))

        # Incidents Key Metrics
        avg_resolution = incidents_data.get('average_resolution_hours')
        avg_text = f"{avg_resolution:.1f} horas" if avg_resolution else "N/A"

        inc_metrics = {
            'Total de Incidentes': f"{incidents_data.get('total_incidents', 0):,}",
            'Incidentes Sin Resolver': f"{incidents_data.get('unresolved_count', 0):,}",
            'Tiempo Promedio de Resolución': avg_text
        }
        elements.extend(self._create_key_metrics(inc_metrics))

        # Incidents by Status
        if incidents_data.get('by_status'):
            inc_status_data = [['Estado', 'Cantidad']]
            status_names = {
                'open': 'Abierto',
                'in_progress': 'En Progreso',
                'resolved': 'Resuelto',
                'closed': 'Cerrado'
            }

            for item in incidents_data['by_status']:
                inc_status_data.append([
                    status_names.get(item['status'], item['status']),
                    f"{item['count']:,}"
                ])

            elements.extend(self._create_summary_table(inc_status_data, "Incidentes por Estado"))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer


# Singleton instance
pdf_generator = PDFReportGenerator()
