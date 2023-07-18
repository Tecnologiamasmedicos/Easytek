
# Tag Manager

Agregar tag manager a los sitios web de Odoo.


## Autor

- [PETI Soluciones Productivas](https://www.peti.com.co)

## Dependencias

Se requieren los modulos

```bash
  website
  website_sale
```
# Documentación

## models

En la carpeta models se encontraran los modelos del modulo.

### Clase `Website`

La clase `Website` hereda del modelo `Model` y agrega un campo para la clave del Google Tag Manager.

```python
class Website(models.Model):

    _inherit = 'website'
    
    google_tag_manager_key = fields.Char(string='Key Google Tag Manager')
```

El campo google_tag_manager_key es de tipo Char y se utiliza para almacenar la clave del Google Tag Manager en la página web.## res_config_settings.py

Este archivo define el modelo `ResConfigSettings`.

### Clase `ResConfigSettings`

La clase `ResConfigSettings` hereda del modelo `TransientModel` y agrega dos campos: `google_tag_manager_key` y `has_google_tag_manager`. Estos campos se utilizan para habilitar el seguimiento de Google Tag Manager en una página web.

```python
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
```

Este método comprueba si hay una clave para el Google Tag Manager y establece el valor de has_google_tag_manager en consecuencia
```python
    @api.depends('website_id')
    def has_google_tag_manager_method(self):
        self.has_google_tag_manager = bool(self.google_tag_manager_key)
```
Este método establece google_tag_manager_key en False si has_google_tag_manager es False
```python
    def inverse_has_google_tag_manager(self):
        if not self.has_google_tag_manager:
            self.google_tag_manager_key = False
```
Este campo relacionado muestra la clave del Google Tag Manager de la página web actual
```python
    google_tag_manager_key = fields.Char(
        related='website_id.google_tag_manager_key',
        readonly=False, string='Key Google Tag Manager')
```

Este campo computado comprueba si hay una clave del Google Tag Manager y permite establecerla en la página web actual
```python
    has_google_tag_manager = fields.Boolean(
        'Google Tag Manager',
        compute=has_google_tag_manager_method,
        inverse=inverse_has_google_tag_manager)
```
## views

En la carpeta views se encontraran las cistas heredadas del modulo.

### `res_config_settings_view.xml`

En este archivo XML se extiende la vista `res.config.settings` para agregar la funcionalidad de Google Tag Manager en Odoo.

 después del campo existente de Google Analytics (`//div[@id='google_analytics_setting']`), condicionalmente mostrar el campo `google_tag_manager_key` basado en el valor del campo `has_google_tag_manager`, y agregar un enlace a la página web de Google Tag Manager.

 ### `templates.xml`

 En este archivo XML, se utiliza la etiqueta <template> para modificar la plantilla del diseño (frontend_layout) en Odoo. Se utiliza la función xpath para insertar el código JavaScript de Google Tag Manager después de la etiqueta <meta> y antes del elemento <div id="wrapwrap">.

 En el script, se define una variable global llamada `dataLayer` y se carga el script de Google Tag Manager con la ID de la cuenta de Google Tag Manager correspondiente. Además, se utiliza la etiqueta `<noscript>` para mostrar una versión sin JavaScript del script de Google Tag Manager.