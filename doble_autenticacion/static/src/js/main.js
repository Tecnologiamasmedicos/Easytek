odoo.define('doble_autenticacion.show_button_code', function(require) {
    'use strict';
    $(function() {
        $("#enviar_codigo").on('click', function(e){
            e.preventDefault()
            if($('#shop').valid()){
                $("#div_warning_code").hide();
                EnviarCodigo(document.querySelector("input[name='email']").value);
            }
        });

        $("#submit_shop").on('click', async function(e){
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
                let dic = await $.ajax({
                    data: {'correo': correo, 'codigo': codigo},
                    url: "/verificar",
                    type: 'get',
                    success: function(data) {
                        return data
                    }
                });
                let diccionario = JSON.parse(dic);
                if(diccionario.correo === 'Correo igual' && diccionario.respuesta === 'Correcto'){
                    $('#shop').submit();
                }else if(diccionario.correo === 'Correo diferente' || diccionario.respuesta === 'Incorrecto'){
                    $(this).html('<span>Siguiente</span><i class="fa fa-chevron-right"/>');
                    $(this).prop('disabled', false);
                    $("#div_warning_code").show();
                }
            }
        });

        $('input[name="email"]').change(function() {
            document.querySelector("input[id='codigo_verificacion']").classList.add("o_hidden");
            document.querySelector("button[id='submit_shop']").classList.add("o_hidden");
            document.querySelector("div[id='input_code']").classList.add("o_hidden");
            document.querySelector("button[id='enviar_codigo']").classList.remove("o_hidden");
        });

        function EnviarCodigo(correo){
            $.ajax({
                data: {'correo': correo},
                url: "/send/code",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);
                    if(decode_data['respuesta'] === 'Correo enviado correctamente'){
                        document.querySelector("input[id='codigo_verificacion']").classList.remove("o_hidden");
                        document.querySelector("div[id='input_code']").classList.remove("o_hidden");
                        document.querySelector("button[id='enviar_codigo']").classList.add("o_hidden");
                        document.querySelector("button[id='submit_shop']").classList.remove("o_hidden");
                    }
                }
            });
        }
    });
});