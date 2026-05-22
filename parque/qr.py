from io import BytesIO

import qrcode
from django.core.files.base import ContentFile


def actualizar_qr(equipo, base_url):
    qr = qrcode.QRCode(box_size=10, border=3)
    qr.add_data(equipo.public_url(base_url))
    qr.make(fit=True)
    image = qr.make_image(fill_color='#063044', back_color='white').convert('RGB')
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    equipo.qr_code.save(f'equipo-{equipo.public_id}.png', ContentFile(buffer.getvalue()), save=False)
    equipo.save(update_fields=['qr_code', 'actualizado_en'])
