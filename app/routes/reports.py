"""Reports routes — generate and download reports."""
from flask import Blueprint, render_template, Response, request
from flask_login import login_required
from app.services.report_service import ReportService

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
def index():
    """Reports page with download options."""
    return render_template('reports/index.html')


@reports_bp.route('/download/<format>')
@login_required
def download(format):
    """Download a report in specified format."""
    period = request.args.get('period', 'daily')

    if format == 'csv':
        data = ReportService.generate_csv_report(period)
        return Response(
            data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=attendance_{period}_report.csv'}
        )
    elif format == 'excel':
        data = ReportService.generate_excel_report(period)
        if data is None:
            return 'Excel generation requires openpyxl', 500
        return Response(
            data,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename=attendance_{period}_report.xlsx'}
        )
    elif format == 'pdf':
        data = ReportService.generate_pdf_report(period)
        if data is None:
            return 'PDF generation requires reportlab', 500
        return Response(
            data,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=attendance_{period}_report.pdf'}
        )
    else:
        return 'Unsupported format', 400
