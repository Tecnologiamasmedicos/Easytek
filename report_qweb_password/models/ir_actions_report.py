import time
import logging
from odoo import fields, models, _
from io import BytesIO
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)
try:
    from PyPDF2 import PdfFileReader, PdfFileWriter
except ImportError as err:
    _logger.debug(err)


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    encrypt = fields.Selection(
        [("manual", "Manual Input Password"),
         ("auto", "Auto Generated Password")],
        string="Encryption",
        help="* Manual Input Password: allow user to key in password on the fly. "
        "This option available only on document print action.\n"
        "* Auto Generated Password: system will auto encrypt password when PDF "
        "created, based on provided python syntax."
    )
    encrypt_password = fields.Char(
        help="Python code syntax to gnerate password.",
    )

    def render_qweb_pdf(self, res_ids=None, data=None):
        """
            Renderiza el informe en formato PDF y realiza la encriptación, si está habilitada.

            :param res_ids: Identificadores de los registros para los cuales se está generando el informe.
            :type res_ids: list or None
            :param data: Datos adicionales para el informe.
            :type data: dict or None
            :return: Datos del PDF renderizado y tipo de contenido.
            :rtype: tuple
        """
        document, ttype = super(IrActionsReport, self).render_qweb_pdf(
            res_ids=res_ids, data=data)
        password = self._get_pdf_password(res_ids[:1])
        document = self._encrypt_pdf(document, password)
        return document, ttype

    def _get_pdf_password(self, res_id):
        """
            Obtiene la contraseña para encriptar el PDF basándose en el método de encriptación elegido.

            :param res_id: Identificador del recurso (registro) para el cual se está generando el PDF.
            :type res_id: int
            :return: Contraseña para encriptar el PDF o False si no se requiere encriptación.
            :rtype: str or False
        """
        encrypt_password = False
        if self.encrypt == "manual":
            # Si se utiliza la acción de impresión del documento, se llama a report_download(),
            # pero no se puede pasar el contexto (encrypt_password) en este lugar.
            # Por lo tanto, el archivo será cifrado nuevamente por report_download().
            # --
            # Lo siguiente se utiliza en caso de que se pase el contexto.
            encrypt_password = self._context.get("encrypt_password", False)
        elif self.encrypt == "auto" and self.encrypt_password:
            obj = self.env[self.model].browse(res_id)
            try:
                encrypt_password = safe_eval(self.encrypt_password,
                                             {'object': obj, 'time': time})
            except:
                raise ValidationError(
                    _("Python code used for encryption password is invalid.\n%s")
                    % self.encrypt_password)
        return encrypt_password

    def _encrypt_pdf(self, data, password):
        """
            Encripta los datos del PDF proporcionados con la contraseña especificada utilizando la biblioteca PyPDF2.

            :param datos: Bytes de los datos originales del PDF que se van a encriptar.
            :type datos: bytes
            :param contraseña: Contraseña utilizada para encriptar el PDF.
            :type contraseña: str
            :return: Datos del PDF encriptado.
            :rtype: bytes
        """
        if not password:
            return data
        output_pdf = PdfFileWriter()
        in_buff = BytesIO(data)
        pdf = PdfFileReader(in_buff)
        output_pdf.appendPagesFromReader(pdf)
        output_pdf.encrypt(password)
        buff = BytesIO()
        output_pdf.write(buff)
        return buff.getvalue()
