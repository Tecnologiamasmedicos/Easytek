odoo.define('doble_autenticacion.show_button_code', function(require) {
    'use strict';
    var ajax = require('web.ajax');

    $(function() {
        $("#reenviar_codigo").on('click', function(e){
            e.preventDefault()
            EnviarCodigo(document.querySelector("input[name='email']").value);
        });

        $("#cerrar").on('click', function(e){
            $("#div_warning_code").hide();
        });

        $("#verificar").on('click', async function(e){
            e.preventDefault();
            if ($("input[name='codigo_verificacion']")[0].value === ''){
                $("#div_warning_code").show();
            }else {
                if($('#shop').valid()){ //checks if it's valid
                    $(this).html('<div><p class="preloader"/><span class="spinner-border spinner-border-sm preloader" role="status" aria-hidden="true" />Cargando...</div>');
                    $(this).prop('disabled', true);
                }
                var correo = document.querySelector("input[name='email']").value;
                var codigo = document.querySelector("input[name='codigo_verificacion']").value
                var data = {'correo': correo, 'codigo': codigo};
                let dic = await ajax.jsonRpc('/verificar', 'call', data)
                     .then(function(data) {
                        return data
                    });
                let diccionario = JSON.parse(dic);
                if(diccionario.correo === 'Correo igual' && diccionario.respuesta === 'Correcto'){
                    $('#shop').submit();
                }else if(diccionario.correo === 'Correo diferente' || diccionario.respuesta === 'Incorrecto'){
                    $(this).html('<span>Verificar</span><i class="fa fa-chevron-right"/>');
                    $(this).prop('disabled', false);
                    $("#div_warning_code").show();
                }
            }
        });

        $("#submit_shop").on('click', function(e){
            e.preventDefault();
            if($('#shop').valid()){ //checks if it's valid
                $(this).html('<div><p class="preloader"/><span class="spinner-border spinner-border-sm preloader" role="status" aria-hidden="true" />Cargando...</div>');
                $(this).prop('disabled', true);
            }
            EnviarCodigo(document.querySelector("input[name='email']").value);
        });

        async function EnviarCodigo(correo){
            var data = {'correo': correo}
            await ajax.jsonRpc('/send/code', 'call', data)
                .then(function(data) {
                    let decode_data = JSON.parse(data);
                    if(decode_data['respuesta'] === 'Correo enviado correctamente'){
                        $("#codigo-verificacion-modal").modal('show');
                        $("#submit_shop").html('<span>Siguiente</span><i class="fa fa-chevron-right"/>');
                        $("#submit_shop").prop('disabled', false);
                    }
                });
        }
    });
});