"""WeasyPrint-based PDF generation for Red Dirt UTV Performance."""
from flask import render_template
from weasyprint import HTML, CSS
import os


def generate_pdf(doc_type: str, ro, app) -> bytes:
    """Render the named template and return PDF bytes."""
    template_map = {
        'intake': 'pdf/intake_form.html',
        'repair_order': 'pdf/repair_order.html',
        'parts_waiver': 'pdf/parts_waiver.html',
        'vehicle_release': 'pdf/vehicle_release.html',
    }
    template_name = template_map[doc_type]

    html_string = render_template(
        template_name,
        ro=ro,
        customer=ro.customer,
        machine=ro.machine,
        shop_name=app.config.get('SHOP_NAME', 'Red Dirt UTV Performance'),
        shop_address=app.config.get('SHOP_ADDRESS', 'Waller, TX'),
        shop_phone=app.config.get('SHOP_PHONE', ''),
        shop_email=app.config.get('SHOP_EMAIL', ''),
    )

    base_url = os.path.join(app.root_path, 'static')
    pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf()
    return pdf_bytes
