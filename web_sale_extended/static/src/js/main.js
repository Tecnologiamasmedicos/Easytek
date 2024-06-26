$('.product_image .img').css('max-width','220px');
$('.product_image .img').css('max-height','123');
$('#submit_beneficiaries').css('margin-top','-220px');

odoo.define('web_sale_extended.show_website_cities', function(require) {
    'use strict';

    $(function() {
        $('#country_address_id').selectpicker();
        $('#type_payment').selectpicker();
        $('#state_address_id').selectpicker('val', '');
        $('#fiscal_position_id').selectpicker();
        $('#city').selectpicker();
        $('#document').selectpicker('val', '');
        $('#fiscal_position').selectpicker();
        $('#bancolombia_types_account').selectpicker();
               
        function consultarZipcode(ciudad){
            $.ajax({
                data: { 'city_id': ciudad },
                url: "/search/zipcodes",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);
                    document.querySelector("input[name='zip']").value = decode_data['data'].zipcode;
                    document.querySelector("input[name='zip_id']").value = decode_data['data'].zipid;
                }
            });
        }

        function consultarPhoneCode(pais){
            $.ajax({
                data: { 'id': pais },
                url: "/search/phonecode",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);
                    document.querySelector("input[name='code_phone']").value = '(+' + decode_data['data'].phonecode + ') ';    
                }
            });
        }
        
        function consultarEstados(pais) {
            $.ajax({
                data: { 'id': pais },
                url: "/search/states",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);                    
                    $('#state_address_id').selectpicker('destroy');
                    $('#state_address_id').empty();
                    $('#city').selectpicker('destroy');
                    $('#city').empty();
                    decode_data.data.states.forEach(function(obj) {
                        $('#state_address_id').append($("<option></option>")
                            .attr("value", obj.state_id).text(obj.state));
                    });
                    let estado = $('#state_address_id').val();
                    let elemento = "select[name='city']";
                    consultarCiudades(estado, elemento);
                    $('#state_address_id').selectpicker('render');
                    $('#city').selectpicker('render');
                    
                }
            });
        }

        $('#city').change(function() {
            let data_select = $("#city option:selected").val();
            let country = $("#country_address_id option:selected").val();
            if(country == 49){
                consultarZipcode(data_select);
            }
            
        });
        
        $('.div_state_text').hide();
        $('.div_city_text').hide();
        
        consultarPhoneCode($("#country_address_id option:selected").val());
        consultarEstados($("#country_address_id option:selected").val());
        
        $('#country_address_id').change(function() {
            let data_select = $("#country_address_id option:selected").val();            
            consultarPhoneCode(data_select);
            if (data_select != 49){  
                document.querySelector("input[name='zip']").value = "";
                document.querySelector("input[name='zip_id']").value = "";
                $('.div_state').hide();
                $('.div_city').hide();
                $('.div_state_text').show();
                $('.div_city_text').show();
            }
            else{ 
                consultarEstados(data_select);                
                $('.div_state_text').hide();
                $('.div_city_text').hide();
                $('.div_state').show();
                $('.div_city').show();   
            }
        });

        function consultarCiudades(estado, elemento) {
            $.ajax({
                data: { 'departamento': estado },
                url: "/search/cities",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);
                    let elemento_completo = $(elemento);
                    $('#city').selectpicker('destroy');
                    $('#city').empty();
                    decode_data.data.cities.forEach(function(obj) {
                        $('#city').append($("<option></option>")
                            .attr("value", obj.city_id).text(obj.city));
                    });
                    $('#city').selectpicker();
                    let data_select = $("#city option:selected").val();
                    consultarZipcode(data_select);
                }
            });
        }

        $("select[name='state_address_id']").on('change', function cambiarEstado() {
            let estado = $(this).val();
            let elemento = "select[name='city']";
            let country = $("#country_address_id option:selected").val();
            if (country == 49){
                consultarCiudades(estado, elemento);
            } else {
                $('#city').selectpicker('destroy');
                $('#city').empty();
                $('#city').append($("<option></option>")
                            .attr("value", '').text('Ciudad...'));
                $('#city').selectpicker();
            }
        });
        
        var partner_id = $("input[name='partner_id']").val();
        var partner_country_id = $("input[name='partner_country_id']").val();
        var partner_state_id = $("input[name='partner_state_id']").val();
        var partner_city_id = $("input[name='partner_city_id']").val();
        var partner_document_type = $("input[name='partner_document_type']").val();
        if (parseInt(partner_id) > 0 && parseInt(partner_city_id) > 0){
            $("select[name='state_id']").val(partner_state_id)
            $("select[name='document']").val(partner_document_type)
            $('#state_address_id').selectpicker('refresh')
            $('#document').selectpicker('refresh')
            consultarCiudades(partner_state_id, partner_city_id);
        }

        $("input[name='bfdate1']").on('change', function calcularEdad() {
            let fecha = $(this).val();
            let hoy = new Date();
            let cumpleanos = new Date(fecha);
            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
            let m = hoy.getMonth() - cumpleanos.getMonth();
            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                edad--;
            }
            let email_asegurador = $("input[name='email']").val();
            let telefono_fijo_asegurador = $("input[name='fijo']").val();
            let celular = $("input[name='phone']").val();
            let ciudad_asegurador = $("input[name='city']").val();
            let adress_asegurador = $("input[name='address']").val();
            let asegurador_state = $("input[name='deparment']").val();
            let country_asegurador = $("input[name='country_id']").val();
            let fiscal_position_asegurador = $("input[name='fiscal_position_id']").val();
            if (edad < 18) {
                console.log("Eres menor de edad");
                $("input[name='bfaddress1']").val(adress_asegurador);
                $("input[name='bffijo1']").val(telefono_fijo_asegurador);
                $("input[name='bfphone1']").val(celular);
            }
        });
        
        $("input[name='bfdate2']").on('change', function calcularEdad() {
            let fecha = $(this).val();
            let hoy = new Date();
            let cumpleanos = new Date(fecha);
            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
            let m = hoy.getMonth() - cumpleanos.getMonth();
            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                edad--;
            }
            let email_asegurador = $("input[name='email']").val();
            let telefono_fijo_asegurador = $("input[name='fijo']").val();
            let celular = $("input[name='phone']").val();
            let ciudad_asegurador = $("input[name='city']").val();
            let adress_asegurador = $("input[name='address']").val();
            let asegurador_state = $("input[name='deparment']").val();
            let country_asegurador = $("input[name='country_id']").val();
            let fiscal_position_asegurador = $("input[name='fiscal_position_id']").val();
            if (edad < 18) {
                console.log("Eres menor de edad");
                $("input[name='bfaddress2']").val(adress_asegurador);
                $("input[name='bffijo2']").val(telefono_fijo_asegurador);
                $("input[name='bfphone2']").val(celular);
            }
        });
        
        
        $("input[name='bfdate3']").on('change', function calcularEdad() {
            let fecha = $(this).val();
            let hoy = new Date();
            let cumpleanos = new Date(fecha);
            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
            let m = hoy.getMonth() - cumpleanos.getMonth();
            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                edad--;
            }
            let email_asegurador = $("input[name='email']").val();
            let telefono_fijo_asegurador = $("input[name='fijo']").val();
            let celular = $("input[name='phone']").val();
            let ciudad_asegurador = $("input[name='city']").val();
            let adress_asegurador = $("input[name='address']").val();
            let asegurador_state = $("input[name='deparment']").val();
            let country_asegurador = $("input[name='country_id']").val();
            let fiscal_position_asegurador = $("input[name='fiscal_position_id']").val();
            if (edad < 18) {
                console.log("Eres menor de edad");
                $("input[name='bfaddress3']").val(adress_asegurador);
                $("input[name='bffijo3']").val(telefono_fijo_asegurador);
                $("input[name='bfphone3']").val(celular);
            }
        });
        
        
        $("input[name='bfdate4']").on('change', function calcularEdad() {
            let fecha = $(this).val();
            let hoy = new Date();
            let cumpleanos = new Date(fecha);
            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
            let m = hoy.getMonth() - cumpleanos.getMonth();
            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                edad--;
            }
            let email_asegurador = $("input[name='email']").val();
            let telefono_fijo_asegurador = $("input[name='fijo']").val();
            let celular = $("input[name='phone']").val();
            let ciudad_asegurador = $("input[name='city']").val();
            let adress_asegurador = $("input[name='address']").val();
            let asegurador_state = $("input[name='deparment']").val();
            let country_asegurador = $("input[name='country_id']").val();
            let fiscal_position_asegurador = $("input[name='fiscal_position_id']").val();
            if (edad < 18) {
                console.log("Eres menor de edad");
                $("input[name='bfaddress4']").val(adress_asegurador);
                $("input[name='bffijo4']").val(telefono_fijo_asegurador);
                $("input[name='bfphone4']").val(celular);
            }
        });
        
        
        $("input[name='bfdate5']").on('change', function calcularEdad() {
            let fecha = $(this).val();
            let hoy = new Date();
            let cumpleanos = new Date(fecha);
            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
            let m = hoy.getMonth() - cumpleanos.getMonth();
            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                edad--;
            }
            let email_asegurador = $("input[name='email']").val();
            let telefono_fijo_asegurador = $("input[name='fijo']").val();
            let celular = $("input[name='phone']").val();
            let ciudad_asegurador = $("input[name='city']").val();
            let adress_asegurador = $("input[name='address']").val();
            let asegurador_state = $("input[name='deparment']").val();
            let country_asegurador = $("input[name='country_id']").val();
            let fiscal_position_asegurador = $("input[name='fiscal_position_id']").val();
            if (edad < 18) {
                console.log("Eres menor de edad");
                $("input[name='bfaddress5']").val(adress_asegurador);
                $("input[name='bffijo5']").val(telefono_fijo_asegurador);
                $("input[name='bfphone5']").val(celular);
            }
        });
        
        
        $("input[name='bfdate6']").on('change', function calcularEdad() {
            let fecha = $(this).val();
            let hoy = new Date();
            let cumpleanos = new Date(fecha);
            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
            let m = hoy.getMonth() - cumpleanos.getMonth();
            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                edad--;
            }
            let email_asegurador = $("input[name='email']").val();
            let telefono_fijo_asegurador = $("input[name='fijo']").val();
            let celular = $("input[name='phone']").val();
            let ciudad_asegurador = $("input[name='city']").val();
            let adress_asegurador = $("input[name='address']").val();
            let asegurador_state = $("input[name='deparment']").val();
            let country_asegurador = $("input[name='country_id']").val();
            let fiscal_position_asegurador = $("input[name='fiscal_position_id']").val();
            if (edad < 18) {
                console.log("Eres menor de edad");
                $("input[name='bfaddress6']").val(adress_asegurador);
                $("input[name='bffijo6']").val(telefono_fijo_asegurador);
                $("input[name='bfphone6']").val(celular);
            }
        });
        
        $.validator.addMethod("formMovilFijoLength", function (value, element) {
            let number = element.value;
            number = number.split(')');
            number = number[number.length - 1].trim();
           if(number.length == 7 || number.length == 10){
              return true;
           } else {
              return false;
           }
        }, "debe tener 7 ó 10 dígitos");
        

        $.validator.addMethod("lettersonly", function(value, element) {
            //return this.optional(element) || /^[a-zA-ZÀ-ÿ\u00f1\u00d1]+(\s*[a-zA-ZÀ-ÿ\u00f1\u00d1]*)*[a-zA-ZÀ-ÿ\u00f1\u00d1]+$/g.test(value);
            return this.optional(element) || /^[a-zA-ZÀ-ÿ\u00f1\u00d1]+(\s*[a-zA-ZÀ-ÿ\u00f1\u00d1]*)*[a-zA-ZÀ-ÿ\u00f1\u00d1]+$/g.test(value.replace(/^\s+|\s+$/g, ''));
        }, "deben ser ser solo letras");
        
        $.validator.addMethod("lettersnumberonly", function(value, element) {
            var document = $("select[name='document']").val();
            if (document == '7' || document == '8') { //pasaporte y documento de identificación extrangera
                return this.optional(element) || /^[A-Za-z0-9]*$/g.test(value);
            }
            return this.optional(element) || /^[0-9]*$/.test(value);
        }, "deben ser ser solo letras");
        
        $.validator.addMethod("documentrange", function(value, element) {
            var document = $("select[name='document']").val();
            if (document == '3') { //cédula de ciudadanía
                if ($.isNumeric(value) && (value < 69999 || value > 9999999999)) {
                    return false;
                } else {
                    return true;
                }
            }
            return true;
        }, "número de documento invalido");
        
        $.validator.addMethod("email2", function(value, element) {
            return this.optional(element) || /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/i.test(value);
        }, "deben contener caracteres válidos");

        $.validator.addMethod("account_numbers_same", function(value, element) {
            let account_number = $("input[name='account_number']").val();
            let confirm_account_number = $("input[name='confirm_account_number']").val();
            if (account_number === confirm_account_number){
                return true;
            }
            return false;
        }, "Los números de cuenta no son iguales");

        $("#shop").validate({
            errorPlacement: function( error, element ) {
                var n = element.attr("name");
                if (n == "document"){
                    error.appendTo('#div_document');
                }
                else if (n == "ada"){
                    error.appendTo('#div_ada');
                }
                else if (n == "tycp"){
                    error.appendTo('#div_tycp');
                }
                else {
                    error.insertAfter(element);
                }
            },
            rules: {
                name: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                lastname: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                othernames: {
                    maxlength: 20,
                    lettersonly: true,
                },
                lastname2: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                email: {
                    required: true,
                    maxlength: 50,
                    email2: true
                },
                phone: {
                    required: true,
                    number: true,
                    formMovilFijoLength: true,
                },
                document: {                    
                    required: true,
                },
                identification_document: {
                    required: true,
                    lettersnumberonly: true,
                    documentrange: true,
                    maxlength: 11,
                    /*
                    min: {
                        depends: function(elem) {
                            var document = $("select[name='document']").val();
                            var identification_document = $("input[name='identification_document']").val();
                            var number = /^[0-9\s]/g;
                            var numberletter= /^[A-Za-z0-9]/g;
                            console.log(document);
                            console.log(identification_document);
                            if (document == '7') { //pasaporte
                                if (/^[A-Za-z0-9]/g.test(identification_document)) {
                                    console.log('ingresando');
                                    return true;
                                }
                                console.log(numberletter.test(identification_document));
                                return false;
                            } else {
                                if (number.test(identification_document) == true) {
                                    return true;
                                }
                                return false;
                            }
                        }
                    },*/
                },
                street: {
                    required: true,
                    minlength: 3,
                    maxlength: 30,
                    formcomma: true,
                },
                state_id_text: {
                    required: true,
                    minlength: 3,
                    maxlength: 30,
                    formcomma: true,
                },
                city_id_text: {
                    required: true,
                    minlength: 3,
                    maxlength: 30,
                    formcomma: true,
                },
                city: {
                    required: true,
                },
                country_address_id: {
                    required: true,
                },
                state_address_id: {
                    required: true,
                },
                aceptacion_datos: {
                    required: true
                },
                tyc: {
                    required: true
                },
                ada: {
                    required: true
                },
                tycp: {
                    required: true
                },
                type_payment: {
                    required: true
                },
                bancolombia_types_account: {
                    required: true
                },
                account_number: {
                    required: true,
                    number: true,
                    minlength: 11,
                    maxlength: 11
                },
                confirm_account_number: {
                    required: true,
                    number: true,
                    account_numbers_same: true,
                    minlength: 11,
                    maxlength: 11
                },
                birthdate_date: {
                    required: true,
                    max: {
                        depends: function(elem) {
                            var edad_maxima = 0;
                            let fecha = $("input[name='birthdate_date']").val();

                            let hoy = new Date();
                            let cumpleanos = new Date(fecha);
                            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
                            let m = hoy.getMonth() - cumpleanos.getMonth();
                            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                                edad--;
                            }
                            return edad > 116
                        }
                    },
                    min: {
                        depends: function(elem) {
                            var edad_maxima = 0;
                            let fecha = $("input[name='birthdate_date']").val();
                            let hoy = new Date();
                            let cumpleanos = new Date(fecha);
                            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
                            let m = hoy.getMonth() - cumpleanos.getMonth();
                            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                                edad--;
                            }
                            return edad < 18
                        }
                    }
                },
                expedition_date: {
                    required: true,
                    max: {
                        depends: function(elem) { 
                            let fecha = $("input[name='expedition_date']").val();
                            let expedition_date = new Date(fecha);
                            let hoy = new Date();
                            if (expedition_date > hoy) {
                                return true;
                            }
                        }
                    },
                    min: {
                        depends: function(elem) {
                            let birthdate_date_form = $("input[name='birthdate_date']").val();
                            let expedition_date_form = $("input[name='expedition_date']").val();
                            let birthdate_date = new Date(birthdate_date_form);
                            let expedition_date = new Date(expedition_date_form);
                            let hoy = new Date();
                            if (expedition_date <= birthdate_date) {
                                return true;
                            }
                        }
                    }
                }
            },
            messages: {
                name: {
                    required: "Tu nombre es requerido",
                    minlength: "Tu nombre debe contener más de 3 caracteres",
                    maxlength: "Tu nombre no puede tener más de 20 caracteres"
                },
                othernames: {
                    maxlength: "Tu nombre no puede tener más de 20 caracteres"                    
                },
                lastname: {
                    required: "Tu apellido es requerido",
                    minlength: "Tu apellido debe contener más de 3 caracteres",
                    maxlength: "Tu apellido debe contener más de 20 caracteres"
                },
                lastname2: {
                    maxlength: "Tu apellido no debe contener más de 20 caracteres"
                },
                email: {
                    required: "Tu email es requerido",
                    maxlength: "Tu email no debe contener más de 50 caracteres",
                    email: "Escribe un email válido",
                    email2: "Escribe un email válido"
                },
                phone: {
                    number: "Este campo solo es numérico",
                    required: "Tu teléfono es requerido",
                    minlength: "Este campo debe tener 10 dígitos",
                    maxlength: "Este campo debe tener 10 dígitos"
                },
                document: {
                    required: "Tu tipo de documento es requerido",
                },
                identification_document: {
                    required: "Tu número de documento es requerido",
                    lettersnumberonly: "Solo números (y letras para pasaporte)",
                    documentrange: "Número de documento invalido",
                    maxlength: "Cantidad de dígitos máxima es de 11",
                },
                street: {
                    required: "Tu dirección es requerida",
                    minlength: "Una dirección contiene más de 3 caracteres",
                    maxlength: "Tu dirección no puede tener más de 30 caracteres",
                },
                city: {
                    required: "Tu ciudad es requerida",
                },
                country_address_id: {
                    required: "Tu país es requerido",
                },
                state_address_id: {
                    required: "Tu departamento es requerido",
                },
                state_id_text: {
                    required: "Tu departamento es requerido",
                },
                city_id_text: {
                    required: "Tu ciudad es requerida",
                },
                aceptacion_datos: {
                    required: "Acepta política de tratamiento de datos para continuar",
                },
                tyc: {
                    required: "Acepta terminos y condiciones para continuar",
                },
                ada: {
                    required: "Acepta débito automático para continuar",
                },
                tycp: {
                    required: "Acepta términos, condiciones y política de tratamiento de datos para continuar",
                },
                type_payment: {
                    required: "El tipo de pago es requerido",
                },
                bancolombia_types_account: {
                    required: "Es necesario que escojas un tipo de cuenta",
                },
                account_number: {
                    required: "Es necesario que escribas tu número de cuenta",
                    number: "Solo se permiten números",
                    minlength: "El número de cuenta debe tener 11 caracteres",
                    maxlength: "El número de cuenta debe tener 11 caracteres"
                },
                confirm_account_number: {
                    required: "Es necesario que escribas tu número de cuenta",
                    number: "Solo se permiten números",
                    minlength: "El número de cuenta debe tener 11 caracteres",
                    maxlength: "El número de cuenta debe tener 11 caracteres"
                },
                birthdate_date: {
                    required: "Tu fecha de nacimiento es requerida",
                    min: "Fecha invalida",
                    max: "Debes de ser menor de 116 años para continuar"
                },
                expedition_date: {
                    required: "Tu fecha de expedición es requerida",
                    min: "Debe ser superior a la fecha de nacimiento",
                    max: "Debe ser igual o inferior a la fecha actual"
                },
            }
        });
        hide_beneficiaries();
    });

    // Coment to open modal module doble_autentication
    // $("#submit_shop").on('click', function(e){
    //     e.preventDefault();
    //     if($('#shop').valid()){ //checks if it's valid
    //         $(this).html('<div><p class="preloader"/><span class="spinner-border spinner-border-sm preloader" role="status" aria-hidden="true" />Cargando...</div>');
    //         $(this).prop('disabled', true);  
    //    }
    //     $('#shop').submit();
    // });

    $('#ada_agree').on('click', function() {
        $("#ada").prop("checked", true);
    });
    
    $('#tycp_agree').on('click', function() {
        $("#tycp").prop("checked", true);
    });

    function hide_beneficiaries() {
        $("#beneficiary1").hide();
        $("#beneficiary2").hide();
        $("#beneficiary3").hide();
        $("#beneficiary4").hide();
        $("#beneficiary5").hide();
        $("#beneficiary6").hide();
    }
    
    
     function llenar(){
        let beneficiary_number = parseInt($("#beneficiaries_number").val());
        for(let i = 1; i <= beneficiary_number; i++){
            $('#cant_beneficiarios').append($("<option></option>").attr("value", i).text(i));
        };
    }
    
    llenar();
    
        

    $("#cant_beneficiarios").on('change', function mostrarbeneficiarios() {
        let cantidad_beneficiarios = parseInt($(this).val());
        if (cantidad_beneficiarios == 0 || cantidad_beneficiarios == '0') {
            hide_beneficiaries();
        } else {
            hide_beneficiaries();
            for (let index = 0; index < cantidad_beneficiarios; index++) {

                let id_elemento = "#beneficiary" + (index + 1);
                let id_subti = "#subti" + (index + 1);
                let subtitulo = "Datos del beneficiario " + (index + 1) + " de " + cantidad_beneficiarios;

                $(id_subti).text(subtitulo);
                $(id_elemento).show();

                //var beneficiaries_number = $("input[name='beneficiaries_number']").val();
                //var beneficiaries_number = $("input[name='beneficiario']").val();

                //alert(cantidad_beneficiarios);

                if (cantidad_beneficiarios == 1){
                    $('#submit_beneficiaries').css('margin-top','-160px');
                } else if (cantidad_beneficiarios == 2){
                    $('#submit_beneficiaries').css('margin-top','-130px');
                } else if (cantidad_beneficiarios == 3){
                    $('#submit_beneficiaries').css('margin-top','-90px');
                } else if (cantidad_beneficiarios == 4){
                    $('#submit_beneficiaries').css('margin-top','-50px');
                } else if (cantidad_beneficiarios == 5){
                    $('#submit_beneficiaries').css('margin-top','-20px');
                } else if (cantidad_beneficiarios == 6){
                    $('#submit_beneficiaries').css('margin-top','20px');
                }

            }
        }
    });
    $("select[name='estado_civil']").on('change', function cambiarConyugues() {
        let estado = $(this).val();
        if (estado == 'Soltero') {
            let newOptions = {
                Seleccione: "",
                Padres: "D",
                Hijos: "H",
                Hermanos: "M"
            };
            for (let index = 0; index < 6; index++) {
                let id_elemento = 'bfparentesco' + (index + 1);
                let elemento = "select[name='" + id_elemento + "']";
                let elemento_completo = $(elemento);
                elemento_completo.empty();
                $.each(newOptions, function(key, value) {
                    elemento_completo.append($("<option></option>")
                        .attr("value", value).text(key));
                });
            }
        } else if (estado == 'Viudo') {
            let newOptions = {
                Seleccione: "",
                Padres: "D",
                Hijos: "H",
                Suegros: "S"
            };
            for (let index = 0; index < 6; index++) {
                let id_elemento = 'bfparentesco' + (index + 1);
                let elemento = "select[name='" + id_elemento + "']";
                let elemento_completo = $(elemento);
                elemento_completo.empty();
                $.each(newOptions, function(key, value) {
                    elemento_completo.append($("<option></option>")
                        .attr("value", value).text(key));
                });
            }
        } else if (estado == 'Divorciado'){
            let newOptions = {
                Seleccione: "",
                Padres: "D",
                Hijos: "H"
            };
            for (let index = 0; index < 6; index++) {
                let id_elemento = 'bfparentesco' + (index + 1);
                let elemento = "select[name='" + id_elemento + "']";
                let elemento_completo = $(elemento);
                elemento_completo.empty();
                $.each(newOptions, function(key, value) {
                    elemento_completo.append($("<option></option>")
                        .attr("value", value).text(key));
                });
            }
        } else {
            let newOptions = {
                Seleccione: "",
                Cónyuge: "C",
                Padres: "D",
                Hijos: "H",
                Suegros: "S"
            };
            for (let index = 0; index < 6; index++) {
                let id_elemento = 'bfparentesco' + (index + 1);
                let elemento = "select[name='" + id_elemento + "']";
                let elemento_completo = $(elemento);
                elemento_completo.empty();
                $.each(newOptions, function(key, value) {
                    elemento_completo.append($("<option></option>")
                        .attr("value", value).text(key));
                });
            }
        }
    });
    
    


       /*
        $('#country_id').change(function() {
            let data_select = $("#country_id option:selected").val();
            if (data_select != '49'){

                $.ajax({
                    data: { 'country': data_select },
                    url: "/search/cities",
                    type: 'get',
                    success: function(data) {
                        alert('llegando')
                    }
                });
            }
        });*/


    function consultarCiudadesBeneficiary(estado, elemento, item) {
        console.log('4');
            $.ajax({
                data: { 'departamento': estado },
                url: "/search/cities",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);
                    let elemento_completo = $(elemento);
                    if (item == 0) {
                        $('#bfcity0').empty();
                        decode_data.data.cities.forEach(function(obj) {
                            $('#bfcity0').append($("<option></option>")
                                .attr("value", obj.city_id).text(obj.city));
                        });
                    } else if (item == 1) {
                        $('#bfcity1').empty();
                        decode_data.data.cities.forEach(function(obj) {
                            $('#bfcity1').append($("<option></option>")
                                .attr("value", obj.city_id).text(obj.city));
                        });
                    } else if (item == 2) {
                        $('#bfcity2').empty();
                        decode_data.data.cities.forEach(function(obj) {
                            $('#bfcity2').append($("<option></option>")
                                .attr("value", obj.city_id).text(obj.city));
                        });
                    } else if (item == 3) {
                        $('#bfcity3').empty();
                        decode_data.data.cities.forEach(function(obj) {
                            $('#bfcity3').append($("<option></option>")
                                .attr("value", obj.city_id).text(obj.city));
                        });
                    } else if (item == 4) {
                        $('#bfcity4').empty();
                        decode_data.data.cities.forEach(function(obj) {
                            $('#bfcity4').append($("<option></option>")
                                .attr("value", obj.city_id).text(obj.city));
                        });
                    }  else if (item == 5) {
                        $('#bfcity5').empty();
                        decode_data.data.cities.forEach(function(obj) {
                            $('#bfcity5').append($("<option></option>")
                                .attr("value", obj.city_id).text(obj.city));
                        });
                    } else if (item == 6) {
                        $('#bfcity6').empty();
                        decode_data.data.cities.forEach(function(obj) {
                            $('#bfcity6').append($("<option></option>")
                                .attr("value", obj.city_id).text(obj.city));
                        });
                    }
                    
                }
            });
        }

    function edad_maxima_asegurado_principal(fecha){
        let cumpleanos = new Date(parseInt(fecha.split('-')[0]),parseInt(fecha.split('-')[1]) - 1,parseInt(fecha.split('-')[2]));
        let fecha_minima = new Date();
        fecha_minima.setDate(fecha_minima.getDate() - 25562);
        fecha_minima = new Date(parseInt(fecha_minima.getFullYear()),parseInt(fecha_minima.getMonth()),parseInt(fecha_minima.getDate()));
        return fecha_minima > cumpleanos
    }

    $("input[name='birthdate_date']").on('change', function calcularEdad() {
        let edad = edad_maxima_asegurado_principal($(this).val());
        if (edad === true) {
            $("#div_warning").show();
        }
        else{
            $("#div_warning").hide();
        }
    });
    
    function obtenerInfoComprador(order_id){
            $.ajax({
                data: { 'order_id': order_id },
                url: "/search/buyer/info",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);
                    if(decode_data['data'].country_id == 49){
                        if(edad_maxima_asegurado_principal(decode_data['data'].birthdate_date) === true){
                            $('#flexCheckDefault').val('0');
                            $('#div_error').html('<button type="button" class="close" data-dismiss="alert" aria-label="Close"><i class="fa fa-times" aria-hidden="false"></i></button>        <strong>Error: El asegurado principal no puede ser mayor a 69 años.');
                            $('#div_error').show();
                            $("#flexCheckDefault").prop("checked", false);
                            $("#flexCheckDefault").attr("disabled", true);
                        }
                        else{
                            document.querySelector("input[name='name']").value = decode_data['data'].firstname;
                            $("input[name='name']").prop('readonly', true);
                            document.querySelector("input[name='othername']").value = decode_data['data'].othernames;
                            $("input[name='othername']").prop('readonly', true);
                            document.querySelector("input[name='lastname']").value = decode_data['data'].lastname;
                            $("input[name='lastname']").prop('readonly', true);
                            document.querySelector("input[name='lastname2']").value = decode_data['data'].lastname2;    
                            $("input[name='lastname2']").prop('readonly', true);                   
                            document.querySelector("input[name='numero_documento']").value = decode_data['data'].identification_document;
                            $("input[name='numero_documento']").prop('readonly', true);
                            document.querySelector("input[name='expedition_date']").value = decode_data['data'].expedition_date;
                            $("input[name='expedition_date']").prop('disabled', true);  
                            document.querySelector("input[name='email']").value = decode_data['data'].email;
                            $("input[name='email']").prop('readonly', true); 

                            if(decode_data['data'].mobile.length > 0){
                                let phone = decode_data['data'].mobile;
                                phone = phone.split(')');
                                let number = phone[phone.length - 1].trim();
                                document.querySelector("input[name='phone']").value = number
                                $("input[name='phone']").prop('readonly', true); 
                            }
                            if(decode_data['data'].phone.length > 0){
                                let phone = decode_data['data'].phone;
                                phone = phone.split(')');
                                let number = phone[phone.length - 1].trim();
                                document.querySelector("input[name='fijo']").value = number
                                $("input[name='fijo']").prop('readonly', true);                             
                            }

                            document.querySelector("input[name='address']").value = decode_data['data'].address;
                            $("input[name='address']").prop('readonly', true); 
                            document.querySelector("input[name='date']").value = decode_data['data'].birthdate_date;    
                            $("input[name='date']").prop('disabled', true); 
                            $("#document_type").val(String(decode_data['data'].document_type_id)).change();
                            $("#document_type").prop('disabled', true); 
                            $("#bfdeparment0").prop('disabled', true); 
                            $("#bfcity0").prop('disabled', true); 
                            $("#bfdeparment0").val(String(decode_data['data'].state_id)).change();
                            setTimeout(() => { $("#bfcity0").val(String(decode_data['data'].city_id)).change(); }, 500);
                        }
                    }                        
                    else{
                        $('#flexCheckDefault').val('0');
                        $('#div_error').html('<button type="button" class="close" data-dismiss="alert" aria-label="Close"><i class="fa fa-times" aria-hidden="false"></i></button>        <strong>Error: País diferente a Colombia</strong> Por el momento solo se presta este servicio en Colombia.');
                        $('#div_error').show();
                        $("#flexCheckDefault").prop("checked", false);
                        $("#flexCheckDefault").attr("disabled", true);
                    }                                   
                }
            });
        }
    
    
    $('#flexCheckDefault').on('click', function() {
        if( $(this).is(':checked') ){
            // Hacer algo si el checkbox ha sido seleccionado
            $(this).val('1');
            let url = window.location.href.split("/");
            let number = url[url.length - 1];
            let order_id = number.split("?")[0];
            obtenerInfoComprador(order_id);
        } else {
            // Hacer algo si el checkbox ha sido deseleccionado
            document.querySelector("input[name='name']").value = "";
            document.querySelector("input[name='othername']").value = "";
            document.querySelector("input[name='lastname']").value = "";
            document.querySelector("input[name='lastname2']").value = "";
            document.querySelector("select[name='document_type']").value = "";
            document.querySelector("input[name='numero_documento']").value = "";
            document.querySelector("input[name='expedition_date']").value = "";
            document.querySelector("input[name='email']").value = "";
            document.querySelector("input[name='phone']").value = "";
            document.querySelector("input[name='fijo']").value = "";
            document.querySelector("input[name='address']").value = "";
            document.querySelector("input[name='date']").value = "";
            $('#bfdeparment0').val('1386').change();
            $(this).val('0');

            $("input[name='name']").prop('readonly', false);           
            $("input[name='othername']").prop('readonly', false);            
            $("input[name='lastname']").prop('readonly', false);           
            $("input[name='lastname2']").prop('readonly', false); 
            $("input[name='numero_documento']").prop('readonly', false); 
            $("input[name='expedition_date']").prop('disabled', false);  
            $("input[name='email']").prop('readonly', false); 
            $("input[name='phone']").prop('readonly', false); 
            $("input[name='fijo']").prop('readonly', false); 
            $("input[name='address']").prop('readonly', false); 
            $("input[name='date']").prop('disabled', false);     
            $("#document_type").prop('disabled', false); 
            $("#bfdeparment0").prop('disabled', false); 
            $("#bfcity0").prop('disabled', false); 
        }
    });
    
    
    $('#bfCheckBox1').on('click', function() {
        if( $(this).is(':checked') ){
            // Hacer algo si el checkbox ha sido seleccionado
            $(this).val('1');
            $("input[name='bfaddress1']").val($("input[name='address']").val());
            $("select[name='bfdeparment1']").val($("select[name='deparment']").val()).change();            
            setTimeout(() => { $("select[name='bfcity1']").val($("select[name='city']").val()).change(); }, 500);
            
            if($("input[name='fijo']").val() > 0){
                $("input[name='bffijo1']").val($("input[name='fijo']").val());
                $("input[name='bffijo1']").prop('readonly', true); 
            }
            
            $("input[name='bfaddress1']").prop('readonly', true);
            $("select[name='bfdeparment1']").prop('disabled', true); 
            $("select[name='bfcity1']").prop('disabled', true); 
        } else {
            // Hacer algo si el checkbox ha sido deseleccionado
            $(this).val('0');
            $("input[name='bfaddress1']").val('');
            $("select[name='bfdeparment1']").val('1386').change();
            $("input[name='bffijo1']").val('');
            
            $("input[name='bfaddress1']").prop('readonly', false);            
            $("select[name='bfdeparment1']").prop('disabled', false); 
            $("select[name='bfcity1']").prop('disabled', false); 
            $("input[name='bffijo1']").prop('readonly', false); 
        }
    });
    
    $('#bfCheckBox2').on('click', function() {
        if( $(this).is(':checked') ){
            // Hacer algo si el checkbox ha sido seleccionado
            $(this).val('1');
            $("input[name='bfaddress2']").val($("input[name='address']").val());
            $("select[name='bfdeparment2']").val($("select[name='deparment']").val()).change();
            setTimeout(() => { $("select[name='bfcity2']").val($("select[name='city']").val()).change(); }, 500);
            
            if($("input[name='fijo']").val() > 0){
                $("input[name='bffijo2']").val($("input[name='fijo']").val());
                $("input[name='bffijo2']").prop('readonly', true); 
            }
            
            $("input[name='bfaddress2']").prop('readonly', true);
            $("select[name='bfdeparment2']").prop('disabled', true); 
            $("select[name='bfcity2']").prop('disabled', true); 
        } else {
            // Hacer algo si el checkbox ha sido deseleccionado
            $(this).val('0');
            $("input[name='bfaddress2']").val('');
            $("select[name='bfdeparment2']").val('1386').change();
            $("input[name='bffijo2']").val('');
            
            $("input[name='bfaddress2']").prop('readonly', false);            
            $("select[name='bfdeparment2']").prop('disabled', false); 
            $("select[name='bfcity2']").prop('disabled', false); 
            $("input[name='bffijo2']").prop('readonly', false); 
        }
    });
    
    $('#bfCheckBox3').on('click', function() {
        if( $(this).is(':checked') ){
            // Hacer algo si el checkbox ha sido seleccionado
            $(this).val('1');
            $("input[name='bfaddress3']").val($("input[name='address']").val());
            $("select[name='bfdeparment3']").val($("select[name='deparment']").val()).change();
            setTimeout(() => { $("select[name='bfcity3']").val($("select[name='city']").val()).change(); }, 500);
            
            if($("input[name='fijo']").val() > 0){
                $("input[name='bffijo3']").val($("input[name='fijo']").val());
                $("input[name='bffijo3']").prop('readonly', true); 
            }
            
            $("input[name='bfaddress3']").prop('readonly', true); 
            $("select[name='bfdeparment3']").prop('disabled', true); 
            $("select[name='bfcity3']").prop('disabled', true); 
        } else {
            // Hacer algo si el checkbox ha sido deseleccionado
            $(this).val('0');
            $("input[name='bfaddress3']").val('');
            $("select[name='bfdeparment3']").val('1386').change();
            $("input[name='bffijo3']").val('');
            
            $("input[name='bfaddress3']").prop('readonly', false);            
            $("select[name='bfdeparment3']").prop('disabled', false); 
            $("select[name='bfcity3']").prop('disabled', false); 
            $("input[name='bffijo3']").prop('readonly', false); 
        }
    });
    
    $('#bfCheckBox4').on('click', function() {
        if( $(this).is(':checked') ){
            // Hacer algo si el checkbox ha sido seleccionado
            $(this).val('1');
            $("input[name='bfaddress4']").val($("input[name='address']").val());
            $("select[name='bfdeparment4']").val($("select[name='deparment']").val()).change();
            setTimeout(() => { $("select[name='bfcity4']").val($("select[name='city']").val()).change(); }, 500);
            
            if($("input[name='fijo']").val() > 0){
                $("input[name='bffijo4']").val($("input[name='fijo']").val());
                $("input[name='bffijo4']").prop('readonly', true); 
            }
            
            $("input[name='bfaddress4']").prop('readonly', true);
            $("select[name='bfdeparment4']").prop('disabled', true); 
            $("select[name='bfcity4']").prop('disabled', true); 
        } else {
            // Hacer algo si el checkbox ha sido deseleccionado
            $(this).val('0');
            $("input[name='bfaddress4']").val('');
            $("select[name='bfdeparment4']").val('1386').change();
            $("input[name='bffijo4']").val('');
            
            $("input[name='bfaddress4']").prop('readonly', false);            
            $("select[name='bfdeparment4']").prop('disabled', false); 
            $("select[name='bfcity4']").prop('disabled', false); 
            $("input[name='bffijo4']").prop('readonly', false); 
        }
    });
    
    $('#bfCheckBox5').on('click', function() {
        if( $(this).is(':checked') ){
            // Hacer algo si el checkbox ha sido seleccionado
            $(this).val('1');
            $("input[name='bfaddress5']").val($("input[name='address']").val());
            $("select[name='bfdeparment5']").val($("select[name='deparment']").val()).change();
            setTimeout(() => { $("select[name='bfcity5']").val($("select[name='city']").val()).change(); }, 500);
            
            if($("input[name='fijo']").val() > 0){
                $("input[name='bffijo5']").val($("input[name='fijo']").val());
                $("input[name='bffijo5']").prop('readonly', true); 
            }
            
            $("input[name='bfaddress5']").prop('readonly', true);
            $("select[name='bfdeparment5']").prop('disabled', true); 
            $("select[name='bfcity5']").prop('disabled', true); 
        } else {
            // Hacer algo si el checkbox ha sido deseleccionado
            $(this).val('0');
            $("input[name='bfaddress5']").val('');
            $("select[name='bfdeparment5']").val('1386').change();
            $("input[name='bffijo5']").val('');
            
            $("input[name='bfaddress5']").prop('readonly', false);            
            $("select[name='bfdeparment5']").prop('disabled', false); 
            $("select[name='bfcity5']").prop('disabled', false); 
            $("input[name='bffijo5']").prop('readonly', false); 
        }
    });
    
    $('#bfCheckBox6').on('click', function() {
        if( $(this).is(':checked') ){
            // Hacer algo si el checkbox ha sido seleccionado
            $(this).val('1');
            $("input[name='bfaddress6']").val($("input[name='address']").val());
            $("select[name='bfdeparment6']").val($("select[name='deparment']").val()).change();
            setTimeout(() => { $("select[name='bfcity6']").val($("select[name='city']").val()).change(); }, 500);
            
            if($("input[name='fijo']").val() > 0){
                $("input[name='bffijo6']").val($("input[name='fijo']").val());
                $("input[name='bffijo6']").prop('readonly', true); 
            }
            
            $("input[name='bfaddress6']").prop('readonly', true);
            $("select[name='bfdeparment6']").prop('disabled', true); 
            $("select[name='bfcity6']").prop('disabled', true); 
        } else {
            // Hacer algo si el checkbox ha sido deseleccionado
            $(this).val('0');
            $("input[name='bfaddress6']").val('');
            $("select[name='bfdeparment6']").val('1386').change();
            $("input[name='bffijo6']").val('');
            
            $("input[name='bfaddress6']").prop('readonly', false);            
            $("select[name='bfdeparment6']").prop('disabled', false); 
            $("select[name='bfcity6']").prop('disabled', false); 
            $("input[name='bffijo6']").prop('readonly', false); 
        }
    });
    
    $("select[id='bfdeparment0']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[id='bfcity0']";
        consultarCiudadesBeneficiary(estado, elemento, 0);

    });
    $("select[name='bfdeparment1']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[name='bfcity1']";
        consultarCiudadesBeneficiary(estado, elemento, 1);

    });
    $("select[name='bfdeparment2']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[name='bfcity2']";
        consultarCiudadesBeneficiary(estado, elemento, 2);

    });
    $("select[name='bfdeparment3']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[name='bfcity3']";
        consultarCiudadesBeneficiary(estado, elemento, 3);

    });
    $("select[name='bfdeparment4']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[name='bfcity4']";
        consultarCiudadesBeneficiary(estado, elemento, 4);

    });
    $("select[name='bfdeparment5']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[name='bfcity5']";
        consultarCiudadesBeneficiary(estado, elemento, 5);

    });
    $("select[name='bfdeparment6']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[name='bfcity6']";
        consultarCiudadesBeneficiary(estado, elemento, 6);

    });

    $("#btn_terminos").click(function() {
        document.getElementById("politica").innerHTML = '';
        document.getElementById("terminos").innerHTML = '<iframe src="/web_sale_extended/static/src/files/terminos.pdf#toolbar=0&navpanes=0&scrollbar=0" width="100%" height="680px"/>';
        $("#terminos").toggle();
    });
    
    $("#btn_politica").click(function() {
        document.getElementById("terminos").innerHTML = '';
        document.getElementById("politica").innerHTML = '<iframe src="/web_sale_extended/static/src/files/tratamiento_de_datos.pdf#toolbar=0&navpanes=0&scrollbar=0" width="100%" height="680px"/>';
        $("#politica").toggle();
    });

    $("#btn_terminos_falabella").click(function() {
        document.getElementById("politica").innerHTML = '';
        document.getElementById("terminos").innerHTML = '<iframe src="/web_sale_extended/static/src/files/falabella.pdf#toolbar=0&navpanes=0&scrollbar=0" width="100%" height="680px"/>';
        $("#terminos").toggle();
    });

    $("#btn_politica_falabella").click(function() {
        document.getElementById("terminos").innerHTML = '';
        document.getElementById("politica").innerHTML = '<iframe src="/web_sale_extended/static/src/files/palig.pdf#toolbar=0&navpanes=0&scrollbar=0" width="100%" height="680px"/>';
        $("#politica").toggle();
    });

    $("#posicion_fiscal_help_icon").on('click', function posicion_fiscal_help() {
        $("#posicion_fiscal_help").toggle();
    });

    $("#posicion_fiscal_help_icon").on('mouseover', function posicion_fiscal_help() {
        $("#posicion_fiscal_help").show();
    });

    // $('#exampleModal').modal();
    // $('#exampleModal').on('shown.bs.modal', function() {
    // $('#myInput').trigger('focus')
    // });

    /* document.getElementById('cant_beneficiarios').addEventListener('change', function() {
         let cantidad_beneficiarios = parseInt(this.value);
         if (cantidad_beneficiarios == 0) {
             hide_beneficiaries();
         } else {
             for (let index = 0; index < cantidad_beneficiarios; index++) {
                 let id_elemento = "#beneficiary" + (index + 1);
                 let id_subti = "#subti" + (index + 1);
                 let subtitulo = "Datos del beneficiario " + (index + 1) + " de " + cantidad_beneficiarios;
                 console.log(subtitulo);
                 $(id_subti).text(subtitulo);
                 $(id_elemento).show();


             }
         }

     });*/
    // var ajax = require('web.ajax');
    // var core = require('web.core');
    // var sAnimation = require('website.content.snippets.animation');

    // var qweb = core.qweb;
    // var _t = core._t;
    // var ajax = require('web.ajax');
    // var dest = 0;

    // sAnimation.registry.OdooWebsiteSearchCity = sAnimation.Class.extend({
    //     selector: ".search-query-city",
    //     autocompleteMinWidth: 300,
    //     init: function() {
    //         console.log('init: search_city');
    //     },
    //     start: function() {
    //         var self = this;

    //         this.$target.attr("autocomplete", "off");
    //         this.$target.parent().addClass("typeahead__container");
    //         this.$target.typeahead({
    //             minLength: 1,
    //             maxItem: 15,
    //             delay: 500,
    //             order: "asc",
    //             cache: false,
    //             hint: true,
    //             accent: true,
    //             //           autofocus: true,
    //             //mustSelectItem: true,
    //             //item: 5334,
    //             //display: ["id","city"],
    //             display: ["city"],
    //             template: '<span>' +
    //                 '<span>{{city}}</span>' +
    //                 '</span>',
    //             source: { city: { url: [{ type: "GET", url: "/search/suggestion_city", data: { query: "{{query}}" }, }, "data.cities"] }, },
    //             callback: {
    //                 onClickAfter: function(node, a, item, event) {
    //                     console.log("CLICK");
    //                 }
    //             }
    //         });
    //     },
    //     debug: true,
    // });

});



odoo.define('web_sale_extended.subscription_add_beneficiaries', function(require) {
    'use strict';

    $(".portal_subscription_beneficiaries_change").on('click', function(e){

      var url_path = '/my/subscription/beneficiaries/';
      var subscription_id = $("input[name='subscription_id']").val();
      var url = url_path + subscription_id;
      window.location.href = url;
    });
    
    $.validator.addMethod("formMovilLength", function (value, element) {
            let number = element.value;
            number = number.split(')');
            number = number[number.length - 1].trim();
           if(number.length == 10 || number.length == 0){
              return true;
           } else {
              return false;
           }
        }, "debe tener 10 dígitos");
        
        $.validator.addMethod("formFijoLength", function (value, element) {
            let number = element.value;
            number = number.split(')');
            number = number[number.length - 1].trim();
           if(number.length == 7 || number.length == 0){
              return true;
           } else {
              return false;
           }
        }, "debe tener 7 dígitos");

    $.validator.addMethod("formcomma", function(value, element) {
        let street = element.value;
        if (street.indexOf(',') != -1){
            return false;
        }
        else{
            return true;
        }
    }, "no puede contener comas");
    
    $.validator.addMethod("lettersonly", function(value, element) {
        return this.optional(element) || /^[a-zA-ZÀ-ÿ\u00f1\u00d1]+(\s*[a-zA-ZÀ-ÿ\u00f1\u00d1]*)*[a-zA-ZÀ-ÿ\u00f1\u00d1]+$/g.test(value.replace(/^\s+|\s+$/g, ''));
    }, "deben ser ser solo letras");
    
    $.validator.addMethod("lettersnumberonly0", function(value, element) {
            var document = $("select[name='document_type']").val();
            if (document == '7' || document == '8') { //pasaporte y documento de identificación extrangera
                return this.optional(element) || /^[A-Za-z0-9]*$/g.test(value);
            } else {
                return this.optional(element) || /^[0-9]*$/.test(value);
            }
        }, "deben ser ser solo letras");
    $.validator.addMethod("lettersnumberonly1", function(value, element) {
            var document = $("select[name='bfdocument1']").val();
            if (document == '7' || document == '8') { //pasaporte y documento de identificación extrangera
                return this.optional(element) || /^[A-Za-z0-9]*$/g.test(value);
            } else {
                return this.optional(element) || /^[0-9]*$/.test(value);
            }
        }, "deben ser ser solo letras");
    $.validator.addMethod("lettersnumberonly2", function(value, element) {
            var document = $("select[name='bfdocument2']").val();
            if (document == '7' || document == '8') { //pasaporte y documento de identificación extrangera
                return this.optional(element) || /^[A-Za-z0-9]*$/g.test(value);
            } else {
                return this.optional(element) || /^[0-9]*$/.test(value);
            }
        }, "deben ser ser solo letras");
    $.validator.addMethod("lettersnumberonly3", function(value, element) {
            var document = $("select[name='bfdocument3']").val();
            if (document == '7' || document == '8') { //pasaporte y documento de identificación extrangera
                return this.optional(element) || /^[A-Za-z0-9]*$/g.test(value);
            } else {
                return this.optional(element) || /^[0-9]*$/.test(value);
            }
        }, "deben ser ser solo letras");
    $.validator.addMethod("lettersnumberonly4", function(value, element) {
            var document = $("select[name='bfdocument4']").val();
            if (document == '7' || document == '8') { //pasaporte y documento de identificación extrangera
                return this.optional(element) || /^[A-Za-z0-9]*$/g.test(value);
            } else {
                return this.optional(element) || /^[0-9]*$/.test(value);
            }
        }, "deben ser ser solo letras");
    $.validator.addMethod("lettersnumberonly5", function(value, element) {
            var document = $("select[name='bfdocument5']").val();
            if (document == '7' || document == '8') { //pasaporte y documento de identificación extrangera
                return this.optional(element) || /^[A-Za-z0-9]*$/g.test(value);
            } else {
                return this.optional(element) || /^[0-9]*$/.test(value);
            }
        }, "deben ser ser solo letras");
    $.validator.addMethod("lettersnumberonly6", function(value, element) {
            var document = $("select[name='bfdocument6']").val();
            if (document == '7' || document == '8') { //pasaporte y documento de identificación extrangera
                return this.optional(element) || /^[A-Za-z0-9]*$/g.test(value);
            } else {
                return this.optional(element) || /^[0-9]*$/.test(value);
            }
        }, "deben ser ser solo letras");
    $.validator.addMethod("documentrange", function(value, element) {
            var document = $("select[name='numero_documento']").val();
            if (document == '3') { //cédula de ciudadanía
                if ($.isNumeric(value) && (value < 69999 || value > 9999999999)) {
                    return false;
                } else {
                    return true;
                }
            }
        }, "número de documento invalido");
    $.validator.addMethod("documentrange1", function(value, element) {
            var document = $("select[name='bfdocument1']").val();
            if (document == '3') { //cédula de ciudadanía
                if ($.isNumeric(value) && (value < 69999 || value > 9999999999)) {
                    return false;
                } else {
                    return true;
                }
            }
            return true;
        }, "número de documento invalido");
    $.validator.addMethod("documentrange2", function(value, element) {
            var document = $("select[name='bfdocument2']").val();
            if (document == '3') { //cédula de ciudadanía
                if ($.isNumeric(value) && (value < 69999 || value > 9999999999)) {
                    return false;
                } else {
                    return true;
                }
            }
            return true;
        }, "número de documento invalido");
    $.validator.addMethod("documentrange3", function(value, element) {
            var document = $("select[name='bfdocument3']").val();
            if (document == '3') { //cédula de ciudadanía
                if ($.isNumeric(value) && (value < 69999 || value > 9999999999)) {
                    return false;
                } else {
                    return true;
                }
            }
            return true;
        }, "número de documento invalido");
    $.validator.addMethod("documentrange4", function(value, element) {
            var document = $("select[name='bfdocument4']").val();
            if (document == '3') { //cédula de ciudadanía
                if ($.isNumeric(value) && (value < 69999 || value > 9999999999)) {
                    return false;
                } else {
                    return true;
                }
            }
            return true;
        }, "número de documento invalido");
    $.validator.addMethod("documentrange5", function(value, element) {
            var document = $("select[name='bfdocument5']").val();
            if (document == '3') { //cédula de ciudadanía
                if ($.isNumeric(value) && (value < 69999 || value > 9999999999)) {
                    return false;
                } else {
                    return true;
                }
            }
            return true;
        }, "número de documento invalido");
    $.validator.addMethod("documentrange6", function(value, element) {
            var document = $("select[name='bfdocument6']").val();
            if (document == '3') { //cédula de ciudadanía
                if ($.isNumeric(value) && (value < 69999 || value > 9999999999)) {
                    return false;
                } else {
                    return true;
                }
            }
            return true;
        }, "número de documento invalido");
    
    $.validator.addMethod("uniquedocument1", function(value, element) {
            var numero_documento = $("input[name='numero_documento']").val();
            var document_type = $("select[name='document_type']").val();
            var bfdocument1 = $("select[name='bfdocument1']").val();
            
            var bfnumero_documento2 = $("input[name='bfnumero_documento2']").val();
            var bfdocument2 = $("select[name='bfdocument2']").val();
            var bfnumero_documento3 = $("input[name='bfnumero_documento3']").val();
            var bfdocument3 = $("select[name='bfdocument3']").val();
            var bfnumero_documento4 = $("input[name='bfnumero_documento4']").val();
            var bfdocument4 = $("select[name='bfdocument4']").val();
            var bfnumero_documento5 = $("input[name='bfnumero_documento5']").val();
            var bfdocument5 = $("select[name='bfdocument5']").val();
            var bfnumero_documento6 = $("input[name='bfnumero_documento6']").val();
            var bfdocument6 = $("select[name='bfdocument6']").val();
            if (value == numero_documento && document_type == bfdocument1) {
                return false;
            }
            if (value == bfnumero_documento2 && bfdocument1 == bfdocument2) {
                return false;
            }
            if (value == bfnumero_documento3 && bfdocument1 == bfdocument3) {
                return false;
            }
            if (value == bfnumero_documento4 && bfdocument1 == bfdocument4) {
                return false;
            }
            if (value == bfnumero_documento5 && bfdocument1 == bfdocument5) {
                return false;
            }
            if (value == bfnumero_documento6 && bfdocument1 == bfdocument6) {
                return false;
            }
            return true;
        }, "número de documento repetido");
    
    $.validator.addMethod("uniquedocument2", function(value, element) {
            var numero_documento = $("input[name='numero_documento']").val();
            var document_type = $("select[name='document_type']").val();
            var bfdocument2 = $("select[name='bfdocument2']").val();
        
            var bfnumero_documento1 = $("input[name='bfnumero_documento1']").val();
            var bfdocument1 = $("select[name='bfdocument1']").val();
            var bfnumero_documento3 = $("input[name='bfnumero_documento3']").val();
            var bfdocument3 = $("select[name='bfdocument3']").val();
            var bfnumero_documento4 = $("input[name='bfnumero_documento4']").val();
            var bfdocument4 = $("select[name='bfdocument4']").val();
            var bfnumero_documento5 = $("input[name='bfnumero_documento5']").val();
            var bfdocument5 = $("select[name='bfdocument5']").val();
            var bfnumero_documento6 = $("input[name='bfnumero_documento6']").val();
            var bfdocument6 = $("select[name='bfdocument6']").val();
            if (value == numero_documento && document_type == bfdocument2) {
                return false;
            }
            if (value == bfnumero_documento1 && bfdocument2 == bfdocument1) {
                return false;
            }
            if (value == bfnumero_documento3 && bfdocument2 == bfdocument3) {
                return false;
            }
            if (value == bfnumero_documento4 && bfdocument2 == bfdocument4) {
                return false;
            }
            if (value == bfnumero_documento5 && bfdocument2 == bfdocument5) {
                return false;
            }
            if (value == bfnumero_documento6 && bfdocument2 == bfdocument6) {
                return false;
            }
            return true;
        }, "número de documento repetido");
    
    $.validator.addMethod("uniquedocument3", function(value, element) {
            var numero_documento = $("input[name='numero_documento']").val();
            var document_type = $("select[name='document_type']").val();
            var bfdocument3 = $("select[name='bfdocument3']").val();
        
            var bfnumero_documento1 = $("input[name='bfnumero_documento1']").val();
            var bfdocument1 = $("select[name='bfdocument1']").val();
            var bfnumero_documento2 = $("input[name='bfnumero_documento2']").val();
            var bfdocument2 = $("select[name='bfdocument2']").val();
            var bfnumero_documento4 = $("input[name='bfnumero_documento4']").val();
            var bfdocument4 = $("select[name='bfdocument4']").val();
            var bfnumero_documento5 = $("input[name='bfnumero_documento5']").val();
            var bfdocument5 = $("select[name='bfdocument5']").val();
            var bfnumero_documento6 = $("input[name='bfnumero_documento6']").val();
            var bfdocument6 = $("select[name='bfdocument6']").val();
            if (value == numero_documento && document_type == bfdocument3) { //cédula de ciudadanía
                return false;
            }
            if (value == bfnumero_documento1 && bfdocument3 == bfdocument1) {
                return false;
            }
            if (value == bfnumero_documento2 && bfdocument3 == bfdocument2) {
                return false;
            }
            if (value == bfnumero_documento4 && bfdocument3 == bfdocument4) {
                return false;
            }
            if (value == bfnumero_documento5 && bfdocument3 == bfdocument5) {
                return false;
            }
            if (value == bfnumero_documento6 && bfdocument3 == bfdocument6) {
                return false;
            }
            return true;
        }, "número de documento repetido");
    
    $.validator.addMethod("uniquedocument4", function(value, element) {
            var numero_documento = $("input[name='numero_documento']").val();
            var document_type = $("select[name='document_type']").val();
            var bfdocument4 = $("select[name='bfdocument4']").val();
        
            var bfnumero_documento1 = $("input[name='bfnumero_documento1']").val();
            var bfdocument1 = $("select[name='bfdocument1']").val();
            var bfnumero_documento2 = $("input[name='bfnumero_documento2']").val();
            var bfdocument2 = $("select[name='bfdocument2']").val();
            var bfnumero_documento3 = $("input[name='bfnumero_documento3']").val();
            var bfdocument3 = $("select[name='bfdocument3']").val();
            var bfnumero_documento5 = $("input[name='bfnumero_documento5']").val();
            var bfdocument5 = $("select[name='bfdocument5']").val();
            var bfnumero_documento6 = $("input[name='bfnumero_documento6']").val();
            var bfdocument6 = $("select[name='bfdocument6']").val();
            if (value == numero_documento && document_type == bfdocument4) { //cédula de ciudadanía
                return false;
            }
            if (value == bfnumero_documento1 && bfdocument4 == bfdocument1) {
                return false;
            }
            if (value == bfnumero_documento2 && bfdocument4 == bfdocument2) {
                return false;
            }
            if (value == bfnumero_documento3 && bfdocument4 == bfdocument3) {
                return false;
            }
            if (value == bfnumero_documento5 && bfdocument4 == bfdocument5) {
                return false;
            }
            if (value == bfnumero_documento6 && bfdocument4 == bfdocument6) {
                return false;
            }
            return true;
        }, "número de documento repetido");
    
    $.validator.addMethod("uniquedocument5", function(value, element) {
            var numero_documento = $("input[name='numero_documento']").val();
            var document_type = $("select[name='document_type']").val();
            var bfdocument5 = $("select[name='bfdocument5']").val();
        
            var bfnumero_documento1 = $("input[name='bfnumero_documento1']").val();
            var bfdocument1 = $("select[name='bfdocument1']").val();
            var bfnumero_documento2 = $("input[name='bfnumero_documento2']").val();
            var bfdocument2 = $("select[name='bfdocument2']").val();
            var bfnumero_documento3 = $("input[name='bfnumero_documento3']").val();
            var bfdocument3 = $("select[name='bfdocument3']").val();
            var bfnumero_documento4 = $("input[name='bfnumero_documento4']").val();
            var bfdocument4 = $("select[name='bfdocument4']").val();
            var bfnumero_documento6 = $("input[name='bfnumero_documento6']").val();
            var bfdocument6 = $("select[name='bfdocument6']").val();
            if (value == numero_documento && document_type == bfdocument5) { //cédula de ciudadanía
                return false;
            }
            if (value == bfnumero_documento1 && bfdocument5 == bfdocument1) {
                return false;
            }
            if (value == bfnumero_documento2 && bfdocument5 == bfdocument2) {
                return false;
            }
            if (value == bfnumero_documento3 && bfdocument5 == bfdocument3) {
                return false;
            }
            if (value == bfnumero_documento4 && bfdocument5 == bfdocument4) {
                return false;
            }
            if (value == bfnumero_documento6 && bfdocument5 == bfdocument6) {
                return false;
            }
            return true;
        }, "número de documento repetido");
    
    $.validator.addMethod("uniquedocument6", function(value, element) {
            var numero_documento = $("input[name='numero_documento']").val();
            var document_type = $("select[name='document_type']").val();
            var bfdocument6 = $("select[name='bfdocument6']").val();
            var bfnumero_documento1 = $("input[name='bfnumero_documento1']").val();
            var bfdocument1 = $("select[name='bfdocument1']").val();
            var bfnumero_documento2 = $("input[name='bfnumero_documento2']").val();
            var bfdocument2 = $("select[name='bfdocument2']").val();
            var bfnumero_documento3 = $("input[name='bfnumero_documento3']").val();
            var bfdocument3 = $("select[name='bfdocument3']").val();
            var bfnumero_documento4 = $("input[name='bfnumero_documento4']").val();
            var bfdocument4 = $("select[name='bfdocument4']").val();
            var bfnumero_documento5 = $("input[name='bfnumero_documento5']").val();
            var bfdocument5 = $("select[name='bfdocument5']").val();
            if (value == numero_documento && document_type == bfdocument6) { //cédula de ciudadanía
                return false;
            }
            if (value == bfnumero_documento1 && bfdocument6 == bfdocument1) {
                return false;
            }
            if (value == bfnumero_documento2 && bfdocument6 == bfdocument2) {
                return false;
            }
            if (value == bfnumero_documento3 && bfdocument6 == bfdocument3) {
                return false;
            }
            if (value == bfnumero_documento4 && bfdocument6 == bfdocument4) {
                return false;
            }
            if (value == bfnumero_documento5 && bfdocument6 == bfdocument5) {
                return false;
            }
            return true;
        }, "número de documento repetido");
    
        $.validator.addMethod("email2", function(value, element) {
            return this.optional(element) || /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/i.test(value);
        }, "deben contener caracteres válidos");

        $.validator.addMethod("uniqueconyuge", function(value, element) {
            let values = [];
            let conyuge_numbers = 0;
            for (let index = 1; index < 7; index++) {
                values.push($("select[name='bfparentesco" + index.toString() + "']").val());
                if($("select[name='bfparentesco" + index.toString() + "']").val() == 'C'){
                    conyuge_numbers = conyuge_numbers + 1;
                }
            }
            if(conyuge_numbers > 1){
                return false;
            }
            else{
                return true;
            }
        }, "No se pueden tener más de un cónyuge");
        
        $.validator.addMethod("twoparents", function(value, element) {
            let values = [];
            let parents_numbers = 0;
            for (let index = 1; index < 7; index++) {
                values.push($("select[name='bfparentesco" + index.toString() + "']").val());
                if($("select[name='bfparentesco" + index.toString() + "']").val() == 'D'){
                    parents_numbers = parents_numbers + 1;
                }
            }
            if(parents_numbers > 2){
                return false;
            }
            else{
                return true;
            }
        }, "No se pueden tener más de dos padres");
    
        $.validator.addMethod("twoinlaws", function(value, element) {
            let values = [];
            let inlaws_numbers = 0;
            for (let index = 1; index < 7; index++) {
                values.push($("select[name='bfparentesco" + index.toString() + "']").val());
                if($("select[name='bfparentesco" + index.toString() + "']").val() == 'S'){
                    inlaws_numbers = inlaws_numbers + 1;
                }
            }
            if(inlaws_numbers > 2){
                return false;
            }
            else{
                return true;
            }
        }, "No se pueden tener más de dos suegros");
    

    $("#beneficiary").validate({
            rules: {
                name: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                lastname: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                othername: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                lastname2: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                email: {
                    required: true,
                    maxlength: 50,
                    email2: true,
                    email: true
                },
                phone: {
                    required: true,
                    number: true,
                    formMovilLength: true,
                },
                ocupation: {
                    maxlength: 12,
                    formcomma: true,
                    lettersonly: true,
                },
                fijo: {
                    // required: false,
                    number: true,
                    formFijoLength: true,
                },
                document_type: {
                    required: true
                },
                sex: {
                    required: true
                },
                estado_civil: {
                    required: true
                },
                numero_documento: {
                    required: true,
                    lettersnumberonly0: true,
                    documentrange: true,
                    maxlength: 11,
                },
                address: {
                    // required: true,
                    minlength: 3,
                    maxlength: 30,
                    formcomma: true,
                },
                city: {
                    // required: true,
                },
                country_address_id: {
                    // required: true,
                },
                deparment: {
                    // required: true,
                },
                state_address_id: {
                    // required: true,
                },
                date: {
                    required: true,
                    max: {
                        depends: function(elem) {
                            let fecha = $("input[name='date']").val();
                            let cumpleanos = new Date(parseInt(fecha.split('-')[0]),parseInt(fecha.split('-')[1]) - 1,parseInt(fecha.split('-')[2]));
                            let fecha_minima = new Date();
                            fecha_minima.setDate(fecha_minima.getDate() - 25562);
                            fecha_minima = new Date(parseInt(fecha_minima.getFullYear()),parseInt(fecha_minima.getMonth()),parseInt(fecha_minima.getDate()));
                            return fecha_minima > cumpleanos
                        }
                    },
                    min: {
                        depends: function(elem) {
                            var edad_maxima = 0;
                            let fecha = $("input[name='date']").val();
                            let hoy = new Date();
                            let cumpleanos = new Date(fecha);
                            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
                            let m = hoy.getMonth() - cumpleanos.getMonth();
                            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                                edad--;
                            }
                            return edad < 18
                        }
                    }
                },
                expedition_date: {
                    required: true,
                    max: {
                        depends: function(elem) { 
                            let fecha = $("input[name='expedition_date']").val();
                            let expedition_date = new Date(fecha);
                            let hoy = new Date();
                            if (expedition_date > hoy) {
                                return true;
                            }
  
                        }
                    },
                    min: {
                        depends: function(elem) {
                            let birthdate_date_form = $("input[name='date']").val();
                            let expedition_date_form = $("input[name='expedition_date']").val();
                            let birthdate_date = new Date(birthdate_date_form);
                            let expedition_date = new Date(expedition_date_form);
                            let hoy = new Date();
                            if (expedition_date <= birthdate_date) {
                                return true;
                            }
                        }
                    }
                },
                // beneficiario1 ///////////////////////////
                bfirstname1: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bflastname1: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bfothername1: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bflastname12: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bfemail1: {
                    // required: true,
                    maxlength: 50,
                    email2: true,
                    email: true
                },
                bfphone1: {
                    required: true,
                    number: true,
                    formMovilLength: true,
                },
                bfocupacion1: {
                    maxlength: 50,
                    formcomma: true,
                    lettersonly: true,
                },
                bffijo1: {
                    // required: false,
                    number: true,
                    formFijoLength: true,
                },
                bfparentesco1: {
                    required: true,
                    uniqueconyuge: true,
                    twoparents: true,
                    twoinlaws: true,
                },
                bfsex1: {
                    required: true
                },
                bfdocument1: {
                    required: true
                },
                bfnumero_documento1: {
                    required: true,
                    maxlength: 11,
                    lettersnumberonly1: true,
                    documentrange1: true,
                    uniquedocument1: true,
                },
                bfaddress1: {
                    // required: true,
                    maxlength: 30,
                    formcomma: true,
                },
                bfcity1: {
                    // required: true,
                },
                bfcountry_id1: {
                    // required: true,
                },
                bfdeparment1: {
                    // required: true,
                },
                bfdate1: {
                    required: true,
                    max: {
                        depends: function(elem) { 
                            let fecha = $("input[name='bfdate1']").val();
                            let hoy = new Date();
                            let cumpleanos = new Date(fecha);
                            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
                            let m = hoy.getMonth() - cumpleanos.getMonth();
                            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                                edad--;
                            }
                            if (cumpleanos > hoy){
                                return true;
                            }
                            return edad > 116
                        }
                    },
                    min: {
                        depends: function(elem) { 
                            let fecha = $("input[name='bfdate1']").val();
                            let fecha_principal = $("input[name='date']").val();
                            let parentesco = $("select[name='bfparentesco1']").val();
                            let birthdate_beneficiary = new Date(fecha);
                            let birthdate_main = new Date(fecha_principal);
                            let hoy = new Date();
                            if (birthdate_beneficiary <= birthdate_main && parentesco == 'H') {
                                return true;
                            }
                        }
                    },
                },
                // beneficiario2 //////////////////////////////////////////
                bfirstname2: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bflastname2: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bfothername2: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bflastname22: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bfemail2: {
                    // required: true,
                    maxlength: 50,
                    email2: true,
                    email: true
                },
                bfphone2: {
                    required: true,
                    number: true,
                    formMovilLength: true,
                },
                bfocupacion2: {
                    maxlength: 50,
                    formcomma: true,
                    lettersonly: true,
                },
                bffijo2: {
                    // required: false,
                    number: true,
                    formFijoLength: true,
                },
                bfparentesco2: {
                    required: true,
                    uniqueconyuge: true,
                    twoparents: true,
                    twoinlaws: true,
                },
                bfsex2: {
                    required: true
                },
                bfdocument2: {
                    required: true
                },
                bfnumero_documento2: {
                    required: true,
                    maxlength: 11,
                    lettersnumberonly2: true,
                    documentrange2: true,
                    uniquedocument2: true,
                },
                bfaddress2: {
                    // required: true,
                    maxlength: 30,
                    formcomma: true,
                },
                bfcity2: {
                    // required: true,
                },
                bfcountry_id2: {
                    // required: true,
                },
                bfdeparment2: {
                    // required: true,
                },
                bfdate2: {
                    required: true,
                    max: {
                        depends: function(elem) { 
                            let fecha = $("input[name='bfdate2']").val();
                            let hoy = new Date();
                            let cumpleanos = new Date(fecha);
                            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
                            let m = hoy.getMonth() - cumpleanos.getMonth();
                            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                                edad--;
                            }
                            if (cumpleanos > hoy){
                                return true;
                            }
                            return edad > 116
                        }
                    },
                    min: {
                        depends: function(elem) { 
                            let fecha = $("input[name='bfdate2']").val();
                            let fecha_principal = $("input[name='date']").val();
                            let parentesco = $("select[name='bfparentesco2']").val();
                            let birthdate_beneficiary = new Date(fecha);
                            let birthdate_main = new Date(fecha_principal);
                            let hoy = new Date();
                            if (birthdate_beneficiary <= birthdate_main && parentesco == 'H') {
                                return true;
                            }
                        }
                    },
                },
                // beneficiario3 //////////////////////////////////////////
                bfirstname3: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bflastname3: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bfothername3: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bflastname32: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bfemail3: {
                    // required: true,
                    maxlength: 50,
                    email2: true,
                    email: true
                },
                bfphone3: {
                    required: true,
                    number: true,
                    formMovilLength: true,
                },
                bfocupacion3: {
                    maxlength: 50,
                    formcomma: true,
                    lettersonly: true,
                },
                bffijo3: {
                    // required: false,
                    number: true,
                    formFijoLength: true,
                },
                bfparentesco3: {
                    required: true,
                    uniqueconyuge: true,
                    twoparents: true,
                    twoinlaws: true,
                },
                bfsex3: {
                    required: true
                },
                bfdocument3: {
                    required: true
                },
                bfnumero_documento3: {
                    required: true,
                    maxlength: 11,
                    lettersnumberonly3: true,
                    documentrange3: true,
                    uniquedocument3: true,
                },
                bfaddress3: {
                    // required: true,
                    maxlength: 30,
                    formcomma: true,
                },
                bfcity3: {
                    // required: true,
                },
                bfcountry_id3: {
                    // required: true,
                },
                bfdeparment3: {
                    // required: true,
                },
                bfdate3: {
                    required: true,
                    max: {
                        depends: function(elem) { 
                            let fecha = $("input[name='bfdate3']").val();
                            let hoy = new Date();
                            let cumpleanos = new Date(fecha);
                            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
                            let m = hoy.getMonth() - cumpleanos.getMonth();
                            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                                edad--;
                            }
                            if (cumpleanos > hoy){
                                return true;
                            }
                            return edad > 116
                        }
                    },
                    min: {
                        depends: function(elem) { 
                            let fecha = $("input[name='bfdate3']").val();
                            let fecha_principal = $("input[name='date']").val();
                            let parentesco = $("select[name='bfparentesco3']").val();
                            let birthdate_beneficiary = new Date(fecha);
                            let birthdate_main = new Date(fecha_principal);
                            let hoy = new Date();
                            if (birthdate_beneficiary <= birthdate_main && parentesco == 'H') {
                                return true;
                            }
                        }
                    },
                },
                // beneficiario4 //////////////////////////////////////////
                bfirstname4: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bflastname4: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bfothername4: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bflastname42: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bfemail4: {
                    // required: true,
                    maxlength: 50,
                    email2: true,
                    email: true
                },
                bfphone4: {
                    required: true,
                    number: true,
                    formMovilLength: true,
                },
                bfocupacion4: {
                    maxlength: 50,
                    formcomma: true,
                    lettersonly: true,
                },
                bffijo4: {
                    // required: false,
                    number: true,
                    formFijoLength: true,
                },
                bfparentesco4: {
                    required: true,
                    uniqueconyuge: true,
                    twoparents: true,
                    twoinlaws: true,
                },
                bfsex4: {
                    required: true
                },
                bfdocument4: {
                    required: true
                },
                bfnumero_documento4: {
                    required: true,
                    maxlength: 11,
                    lettersnumberonly4: true,
                    documentrange4: true,
                    uniquedocument4: true,
                },
                bfaddress4: {
                    // required: true,
                    maxlength: 30,
                    formcomma: true,
                },
                bfcity4: {
                    // required: true,
                },
                bfcountry_id4: {
                    // required: true,
                },
                bfdeparment4: {
                    // required: true,
                },
                bfdate4: {
                    required: true,
                    max: {
                        depends: function(elem) { 
                            let fecha = $("input[name='bfdate4']").val();
                            let hoy = new Date();
                            let cumpleanos = new Date(fecha);
                            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
                            let m = hoy.getMonth() - cumpleanos.getMonth();
                            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                                edad--;
                            }
                            if (cumpleanos > hoy){
                                return true;
                            }
                            return edad > 116
                        }
                    },
                    min: {
                        depends: function(elem) { 
                            let fecha = $("input[name='bfdate4']").val();
                            let fecha_principal = $("input[name='date']").val();
                            let parentesco = $("select[name='bfparentesco4']").val();
                            let birthdate_beneficiary = new Date(fecha);
                            let birthdate_main = new Date(fecha_principal);
                            let hoy = new Date();
                            if (birthdate_beneficiary <= birthdate_main && parentesco == 'H') {
                                return true;
                            }
                        }
                    },
                },
                // beneficiario5 //////////////////////////////////////////
                bfirstname5: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bflastname5: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bfothername5: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bflastname52: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bfemail5: {
                    // required: true,
                    maxlength: 50,
                    email2: true,
                    email: true
                },
                bfphone5: {
                    required: true,
                    number: true,
                    formMovilLength: true,
                },
                bfocupacion5: {
                    maxlength: 50,
                    formcomma: true,
                    lettersonly: true,
                },
                bffijo5: {
                    // required: false,
                    number: true,
                    formFijoLength: true,
                },
                bfparentesco5: {
                    required: true,
                    uniqueconyuge: true,
                    twoparents: true,
                    twoinlaws: true,
                },
                bfsex5: {
                    required: true
                },
                bfdocument5: {
                    required: true
                },
                bfnumero_documento5: {
                    required: true,
                    maxlength: 11,
                    lettersnumberonly5: true,
                    documentrange5: true,
                    uniquedocument5: true,
                },
                bfaddress5: {
                    // required: true,
                    maxlength: 30,
                    formcomma: true,
                },
                bfcity5: {
                    // required: true,
                },
                bfcountry_id5: {
                    // required: true,
                },
                bfdeparment5: {
                    // required: true,
                },
                bfdate5: {
                    required: true,
                    max: {
                        depends: function(elem) { 
                            let fecha = $("input[name='bfdate5']").val();
                            let hoy = new Date();
                            let cumpleanos = new Date(fecha);
                            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
                            let m = hoy.getMonth() - cumpleanos.getMonth();
                            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                                edad--;
                            }
                            if (cumpleanos > hoy){
                                return true;
                            }
                            return edad > 116
                        }
                    },
                    min: {
                        depends: function(elem) { 
                            let fecha = $("input[name='bfdate5']").val();
                            let fecha_principal = $("input[name='date']").val();
                            let parentesco = $("select[name='bfparentesco5']").val();
                            let birthdate_beneficiary = new Date(fecha);
                            let birthdate_main = new Date(fecha_principal);
                            let hoy = new Date();
                            if (birthdate_beneficiary <= birthdate_main && parentesco == 'H') {
                                return true;
                            }
                        }
                    },
                },
                // beneficiario6 //////////////////////////////////////////
                bfirstname6: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bflastname6: {
                    required: true,
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bfothername6: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bflastname62: {
                    minlength: 3,
                    maxlength: 20,
                    lettersonly: true,
                },
                bfemail6: {
                    // required: true,
                    maxlength: 50,
                    email2: true,
                    email: true
                },
                bfphone6: {
                    required: true,
                    number: true,
                    formMovilLength: true,
                },
                bfocupacion6: {
                    maxlength: 50,
                    formcomma: true,
                    lettersonly: true,
                },
                bffijo6: {
                    // required: false,
                    number: true,
                    formFijoLength: true,
                },
                bfparentesco6: {
                    required: true,
                    uniqueconyuge: true,
                    twoparents: true,
                    twoinlaws: true,
                },
                bfsex6: {
                    required: true
                },
                bfdocument6: {
                    required: true
                },
                bfnumero_documento6: {
                    required: true,
                    maxlength: 11,
                    lettersnumberonly6: true,
                    documentrange6: true,
                    uniquedocument6: true,
                },
                bfaddress6: {
                    // required: true,
                    maxlength: 30,
                    formcomma: true,
                },
                bfcity6: {
                    // required: true,
                },
                bfcountry_id6: {
                    // required: true,
                },
                bfdeparment6: {
                    // required: true,
                },
                bfdate6: {
                    required: true,
                    max: {
                        depends: function(elem) { 
                            let fecha = $("input[name='bfdate6']").val();
                            let hoy = new Date();
                            let cumpleanos = new Date(fecha);
                            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
                            let m = hoy.getMonth() - cumpleanos.getMonth();
                            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                                edad--;
                            }
                            if (cumpleanos > hoy){
                                return true;
                            }
                            return edad > 116
                        }
                    },
                    min: {
                        depends: function(elem) { 
                            let fecha = $("input[name='bfdate6']").val();
                            let fecha_principal = $("input[name='date']").val();
                            let parentesco = $("select[name='bfparentesco6']").val();
                            let birthdate_beneficiary = new Date(fecha);
                            let birthdate_main = new Date(fecha_principal);
                            let hoy = new Date();
                            if (birthdate_beneficiary <= birthdate_main && parentesco == 'H') {
                                return true;
                            }
                        }
                    },
                },
                ////////////////////////////////////////////
            },
            messages: {
                name: {
                    required: "un nombre es requerido",
                    minlength: "un nombre contiene más de 3 caracteres",
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                },
                othername: {
                    minlength: "un nombre contiene más de 3 caracteres",
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                }, 
                lastname2: {
                    minlength: "un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                lastname: {
                    required: "un apellido es requerido",
                    minlength: "un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                email: {
                    required: "un email es requerido",
                    maxlength: "el correo electrónico no debe contener más de 50 caracteres",
                    email2: "escribe un email válido",
                    email: "escribe un email válido"
                },
                phone: {
                    number: "este campo solo es numérico",
                    required: "un teléfono es requerido",                    
                },
                ocupation: {
                    maxlength: "no puede contener más de 12 caracteres"
                },
                fijo: {
                    minlength: "debe tener 7 dígitos",
                    maxlength: "debe tener 7 dígitos"
                },
                sex: {
                    required: "este campo es requerido",
                },
                document_type: {
                    required: "un tipo de documento es requerido",
                },
                estado_civil: {
                    required: "un estado civil es requerido",
                },
                numero_documento: {
                    required: "un número de documento es requerido",
                    maxlength: "cantidad de dígitos maxima es de 11",
                    lettersnumberonly0: "solo números (y letras para pasaporte)",
                    documentrange: "número de documento invalido",
                    uniquedocument: "número de documento repetido",
                },
                address: {
                    required: "una dirección es requerida",
                    minlength: "una dirección contiene más de 3 caracteres",
                    maxlength: "tu dirección no puede tener más de 30 caracteres",
                },
                city: {
                    required: "una ciudad es requerida",
                },
                country_address_id: {
                    required: "un país es requerido",
                },
                deparment: {
                    required: "un departamento es requerido",
                },
                state_address_id: {
                    required: "un departamento es requerido",
                },
                date: {
                    required: "una fecha de nacimiento es requerido",
                    min: "fecha invalida",
                    max: "debes de ser menor de 69 años para continuar"
                },
                expedition_date: {
                    required: "tu fecha de expedición es requerido",
                    min: "debe ser superior a la fecha de nacimiento",
                    max: "debe ser igual o inferior a la fecha actual"
                },
                ////////////////////////////////////////////
                bfirstname1: {
                    required: "un nombre es requerido",
                    minlength: "un nombre contiene más de 3 caracteres",
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                },
                bfothername1: {
                    minlength: "un nombre contiene más de 3 caracteres",
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                }, 
                bflastname12: {
                    minlength: "un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                bflastname1: {
                    required: "un apellido es requerido",
                    minlength: "un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                bfemail1: {
                    required: "un email es requerido",
                    maxlength: "el correo electronico no debe contener más de 50 caracteres",
                    email2: "escribe un email válido",
                    email: "escribe un email válido"
                },
                bfphone1: {
                    number: "este campo solo es numérico",
                    required: "un teléfono es requerido",
                },
                bfocupacion1: {
                    maxlength: "no puede contener más de 50 caracteres"
                },
                bffijo1: {           
                    number: "este campo solo es numérico",
                    minlength: "debe tener 7 dígitos",
                    maxlength: "debe tener 7 dígitos"
                },
                bfsex1: {
                    required: "este campo es requerido",
                },
                bfparentesco1: {
                    required: "un parentesco de documento es requerido",
                },
                bfdocument1: {
                    required: "un tipo de documento es requerido",
                },
                bfnumero_documento1: {
                    required: "un número de documento es requerido",
                    maxlength: "cantidad de dígitos maxima es de 11",
                    lettersnumberonly1: "solo números (y letras para pasaporte)",
                    documentrange1: "número de documento invalido",
                    uniquedocument1: "número de documento repetido",
                },
                bfaddress1: {
                    required: "una dirección es requerida",
                    minlength: "una dirección contiene más de 3 caracteres",
                    maxlength: "tu dirección no puede tener más de 30 caracteres",
                },
                bfcity1: {
                    required: "una ciudad es requerida",
                },
                bfcountry_id1: {
                    required: "un país es requerido",
                },
                bfdeparment1: {
                    required: "un departamento es requerido",
                },
                bfdate1: {
                    required: "una fecha de nacimiento es requerido",
                    max: "debe tener una edad entre 0 y 116 años",
                    min: "tú hijo no puede ser mayor a ti"
                },
                ////////////////////////////////////////////
                bfirstname2: {
                    required: "un nombre es requerido",
                    minlength: "un nombre contiene más de 3 caracteres",                    
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                },
                bfothername2: {
                    minlength: "un nombre contiene más de 3 caracteres",
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                }, 
                bflastname22: {
                    minlength: "un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                bflastname2: {
                    required: "un apellido es requerido",
                    minlength: "un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                bfemail2: {
                    required: "un email es requerido",
                    maxlength: "el correo electronico no debe contener más de 50 caracteres",
                    email2: "escribe un email válido",
                    email: "escribe un email válido"
                },
                bfphone2: {
                    number: "este campo solo es numérico",
                    required: "un teléfono es requerido",                    
                },
                bfocupacion2: {
                    maxlength: "no puede contener más de 50 caracteres"
                },
                bffijo2: {
                    number: "este campo solo es numérico",
                    minlength: "debe tener 7 dígitos",
                    maxlength: "debe tener 7 dígitos"
                },
                bfsex2: {
                    required: "este campo es requerido",
                },
                bfparentesco2: {
                    required: "un parentesco de documento es requerido",
                },
                bfdocument2: {
                    required: "un tipo de documento es requerido",
                },
                bfnumero_documento2: {
                    required: "un número de documento es requerido",
                    maxlength: "cantidad de dígitos maxima es de 11",
                    lettersnumberonly2: "solo números (y letras para pasaporte)",
                    documentrange2: "número de documento invalido",
                    uniquedocument2: "número de documento repetido",
                },
                bfaddress2: {
                    required: "una dirección es requerida",
                    minlength: "una dirección contiene más de 3 caracteres",
                    maxlength: "tu dirección no puede tener más de 30 caracteres",
                },
                bfcity2: {
                    required: "una ciudad es requerida",
                },
                bfcountry_id2: {
                    required: "un país es requerido",
                },
                bfdeparment2: {
                    required: "un departamento es requerido",
                },
                bfdate2: {
                    required: "una fecha de nacimiento es requerido",
                    max: "debe tener una edad entre 0 y 116 años",
                    min: "tú hijo no puede ser mayor a ti"
                },
                ////////////////////////////////////////////
                bfirstname3: {
                    required: "tu nombre es requerido",
                    minlength: "Un nombre contiene más de 3 caracteres",
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                },                
                bfothername3: {
                    minlength: "un nombre contiene más de 3 caracteres",
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                }, 
                bflastname32: {
                    minlength: "un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                bflastname3: {
                    required: "tu apellido es requerido",
                    minlength: "Un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                bfemail3: {
                    required: "tu email es requerido",
                    maxlength: "el correo electronico no debe contener más de 50 caracteres",
                    email2: "Escribe un email válido",
                    email: "escribe un email válido"
                },
                bfphone3: {
                    number: "este campo solo es numérico",
                    required: "tu teléfono es requerido", 
                },
                bfocupacion3: {
                    maxlength: "no puede contener más de 50 caracteres"
                },
                bffijo3: {
                    number: "este campo solo es numérico",
                    minlength: "debe tener 7 dígitos",
                    maxlength: "debe tener 7 dígitos"
                },
                bfsex3: {
                    required: "este campo es requerido",
                },
                bfparentesco3: {
                    required: "un parentesco de documento es requerido",
                },
                bfdocument3: {
                    required: "tu tipo de documento es requerido",
                },
                bfnumero_documento3: {
                    required: "tu número de documento es requerido",
                    maxlength: "cantidad de dígitos maxima es de 11",
                    lettersnumberonly3: "solo números (y letras para pasaporte)",
                    documentrange3: "número de documento invalido",
                    uniquedocument3: "número de documento repetido",
                },
                bfaddress3: {
                    required: "tu dirección es requerido",
                    minlength: "una dirección contiene más de 3 caracteres",
                    maxlength: "tu dirección no puede tener más de 30 caracteres",
                },
                bfcity3: {
                    required: "tu ciudad es requerido",
                },
                bfcountry_id3: {
                    required: "Este campo es requerido",
                },
                bfdeparment3: {
                    required: "tu departamento es requerido",
                },
                bfdate3: {
                    required: "tu fecha de nacimiento es requerido",
                    max: "debe tener una edad entre 0 y 116 años",
                    min: "tú hijo no puede ser mayor a ti"
                },
                ////////////////////////////////////////////
                bfirstname4: {
                    required: "tu nombre es requerido",
                    minlength: "Un nombre contiene más de 3 caracteres",
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                },
                bfothername4: {
                    minlength: "un nombre contiene más de 3 caracteres",
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                }, 
                bflastname42: {
                    minlength: "un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                bflastname4: {
                    required: "tu apellido es requerido",
                    minlength: "Un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                bfemail4: {
                    required: "tu email es requerido",
                    maxlength: "el correo electronico no debe contener más de 50 caracteres",
                    email2: "Escribe un email válido",
                    email: "escribe un email válido"
                },
                bfphone4: {
                    number: "este campo solo es numérico",
                    required: "tu teléfono es requerido",
                },
                bfocupacion4: {
                    maxlength: "no puede contener más de 50 caracteres"
                },
                bffijo4: {
                    number: "este campo solo es numérico",
                    minlength: "debe tener 7 dígitos",
                    maxlength: "debe tener 7 dígitos"
                },
                bfsex4: {
                    required: "este campo es requerido",
                },
                bfparentesco4: {
                    required: "un parentesco de documento es requerido",
                },
                bfdocument4: {
                    required: "tu tipo de documento es requerido",
                },
                bfnumero_documento4: {
                    required: "tu número de documento es requerido",
                    maxlength: "cantidad de dígitos maxima es de 11",
                    lettersnumberonly4: "solo números (y letras para pasaporte)",
                    documentrange4: "número de documento invalido",
                    uniquedocument4: "número de documento repetido",
                },
                bfaddress4: {
                    required: "tu dirección es requerido",
                    minlength: "una dirección contiene más de 3 caracteres",
                    maxlength: "tu dirección no puede tener más de 30 caracteres",
                },
                bfcity4: {
                    required: "tu ciudad es requerido",
                },
                bfcountry_id4: {
                    required: "Este campo es requerido",
                },
                bfdeparment4: {
                    required: "tu departamento es requerido",
                },
                bfdate4: {
                    required: "tu fecha de nacimiento es requerido",
                    max: "debe tener una edad entre 0 y 116 años",
                    min: "tú hijo no puede ser mayor a ti"
                },
                ////////////////////////////////////////////
                bfirstname5: {
                    required: "tu nombre es requerido",
                    minlength: "Un nombre contiene más de 3 caracteres",
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                },
                bfothername5: {
                    minlength: "un nombre contiene más de 3 caracteres",
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                }, 
                bflastname52: {
                    minlength: "un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                bflastname5: {
                    required: "tu apellido es requerido",
                    minlength: "Un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                bfemail5: {
                    required: "tu email es requerido",
                    maxlength: "el correo electronico no debe contener más de 50 caracteres",
                    email2: "Escribe un email válido",
                    email: "escribe un email válido"
                },
                bfphone5: {
                    number: "este campo solo es numérico",
                    required: "tu teléfono es requerido", 
                },
                bfocupacion5: {
                    maxlength: "no puede contener más de 50 caracteres"
                },
                bffijo5: {
                    number: "este campo solo es numérico",
                    minlength: "debe tener 7 dígitos",
                    maxlength: "debe tener 7 dígitos"
                },
                bfsex5: {
                    required: "este campo es requerido",
                },
                bfparentesco5: {
                    required: "un parentesco de documento es requerido",
                },
                bfdocument5: {
                    required: "tu tipo de documento es requerido",
                },
                bfnumero_documento5: {
                    required: "tu número de documento es requerido",                    
                    maxlength: "cantidad de dígitos maxima es de 11",
                    lettersnumberonly5: "solo números (y letras para pasaporte)",
                    documentrange5: "número de documento invalido",
                    uniquedocument5: "número de documento repetido",
                },
                bfaddress5: {
                    required: "tu dirección es requerido",
                    minlength: "una dirección contiene más de 3 caracteres",
                    maxlength: "tu dirección no puede tener más de 30 caracteres",
                },
                bfcity5: {
                    required: "tu ciudad es requerido",
                },
                bfcountry_id5: {
                    required: "Este campo es requerido",
                },
                bfdeparment5: {
                    required: "tu departamento es requerido",
                },
                bfdate5: {
                    required: "tu fecha de nacimiento es requerido",
                    max: "debe tener una edad entre 0 y 116 años",
                    min: "tú hijo no puede ser mayor a ti"
                },
                ////////////////////////////////////////////
                bfirstname6: {
                    required: "tu nombre es requerido",
                    minlength: "Un nombre contiene más de 3 caracteres",
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                },
                bfothername6: {
                    minlength: "un nombre contiene más de 3 caracteres",
                    maxlength: "un nombre no debe contener más de 20 caracteres"
                }, 
                bflastname62: {
                    minlength: "un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                bflastname6: {
                    required: "tu apellido es requerido",
                    minlength: "Un apellido contiene más de 3 caracteres",
                    maxlength: "un apellido no debe contener más de 20 caracteres"
                },
                bfemail6: {
                    required: "tu email es requerido",
                    maxlength: "el correo electronico no debe contener más de 50 caracteres",
                    email2: "Escribe un email válido",
                    email: "escribe un email válido"
                },
                bfphone6: {
                    number: "este campo solo es numérico",
                    required: "tu teléfono es requerido",
                },
                bfocupacion6: {
                    maxlength: "no puede contener más de 50 caracteres"
                },
                bffijo6: {
                    number: "este campo solo es numérico",
                    minlength: "debe tener 7 dígitos",
                    maxlength: "debe tener 7 dígitos"
                },
                bfsex6: {
                    required: "este campo es requerido",
                },
                bfparentesco6: {
                    required: "un parentesco de documento es requerido",
                },
                bfdocument6: {
                    required: "tu tipo de documento es requerido",
                },
                bfnumero_documento6: {
                    required: "tu número de documento es requerido",
                    maxlength: "cantidad de dígitos maxima es de 11",
                    lettersnumberonly6: "solo números (y letras para pasaporte)",
                    documentrange6: "número de documento invalido",
                    uniquedocument6: "número de documento repetido",
                },
                bfaddress6: {
                    required: "tu dirección es requerido",
                    minlength: "una dirección contiene más de 3 caracteres",
                    maxlength: "tu dirección no puede tener más de 30 caracteres",
                },
                bfcity6: {
                    required: "tu ciudad es requerido",
                },
                bfcountry_id6: {
                    required: "Este campo es requerido",
                },
                bfdeparment6: {
                    required: "tu departamento es requerido",
                },
                bfdate6: {
                    required: "tu fecha de nacimiento es requerido",
                    max: "debe tener una edad entre 0 y 116 años",
                    min: "tú hijo no puede ser mayor a ti"
                },
            }
        });
    
    let estado_civil = $("select[name='estado_civil']").val();
    if (estado_civil == 'Soltero') {
        let newOptions = {
            Seleccione: "",
            Padres: "D",
            Hijos: "H",
            Hermanos: "M"
        };
        for (let index = 0; index < 6; index++) {
            let id_elemento = 'bfparentesco' + (index + 1);
            let elemento = "select[name='" + id_elemento + "']";
            let elemento_completo = $(elemento);
            elemento_completo.empty();
            $.each(newOptions, function(key, value) {
                elemento_completo.append($("<option></option>")
                    .attr("value", value).text(key));
            });
        }
    }
    if (estado_civil == 'Viudo') {
        let newOptions = {
            Seleccione: "",
            Padres: "D",
            Hijos: "H",
            Hermanos: "M",
            Suegros: "S"
        };
        for (let index = 0; index < 6; index++) {
            let id_elemento = 'bfparentesco' + (index + 1);
            let elemento = "select[name='" + id_elemento + "']";
            let elemento_completo = $(elemento);
            elemento_completo.empty();
            $.each(newOptions, function(key, value) {
                elemento_completo.append($("<option></option>")
                    .attr("value", value).text(key));
            });
        }
    }
    if (estado_civil == 'Divorciado'){
        let newOptions = {
            Seleccione: "",
            Padres: "D",
            Hijos: "H"
        };
        for (let index = 0; index < 6; index++) {
            let id_elemento = 'bfparentesco' + (index + 1);
            let elemento = "select[name='" + id_elemento + "']";
            let elemento_completo = $(elemento);
            elemento_completo.empty();
            $.each(newOptions, function(key, value) {
                elemento_completo.append($("<option></option>")
                    .attr("value", value).text(key));
            });
        }
    }
    
    // Valida si el beneficiario principal ya posee una
    // poliza activa ('PEDIDO DE VENTA' o 'ESPERANDO APROBACION')
    // retorna true en caso de no poseer polizas
    // retorna false si posee al menos una poliza
    function validaPolizaUnicaBancolombia () {
        var numero_documento
        if (document.querySelector('#primary_insured #numero_documento')) {
            numero_documento = document.querySelector('#primary_insured #numero_documento').value
        }

        // Si ya ha digitado el numero del documento del beneficiario principal
        // >> entonces busca si ya posee polizas
        if (numero_documento) {
            var unique_buyer = false
            $.ajax({
                url: '/unique/buyer/bancolombia/' + numero_documento,
                type: 'GET',
                dataType: 'json',
                async: false,
            })
            .done(function(res) {
                // console.log("success");
                // console.log(res);
                if (res.unique) {
                    unique_buyer = res.unique[0]
                }
            })
            .fail(function(res) {
                console.log("error");
                console.log(res);
            })
        }

        if (unique_buyer == false) {
            let errorLabel = document.createElement("label");
            errorLabel.innerHTML = 'Esta persona ya posee una póliza activa. Solo se permite una póliza por asegurado.'
            errorLabel.classList.add('error')
            document.querySelector('#form-group-numero_documento').append(errorLabel)
            return unique_buyer
        }        
    }

    if ($('#submit_beneficiaries').length) {
        $("#submit_beneficiaries").on('click', function(e){
            e.preventDefault();

            // Valida poliza unica
            if (validaPolizaUnicaBancolombia() == false) {
                return false
            }

            if($('#beneficiary').valid()){ //checks if it's valid
                $(this).html('<div><p class="preloader"/><span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" />Cargando...</div>');
                $(this).prop('disabled', true);  
            }

            // Enviar al dar clic en el btn de "agregar beneficiario" y "generar orden de compra"
            if (e.target.classList.contains("btn-bancolombia-beneficiaries")) {
                var elementText = e.target.innerText // in a and button tags
                dataLayer.push({
                    event:"SEND_BOTONES_PALIG",
                    activo:window.location.href, // ejemplo: 'palig'
                    seccion:"seguros",
                    nombreFlujo:"plan familia protegida",
                    path:"/palig/plan-familia-protegida/asegurado",
                    nombrePaso:"datos",
                    paso:2,
                    elemento:elementText
                })
            }

            $('#beneficiary').submit();
        });

        $("#primary_insured #numero_documento").on('focusout', function(e){
            validaPolizaUnicaBancolombia()
        });
    }
});


odoo.define('web_sale_extended.welcome_masmedicos', function(require) {
    'use strict';
    
    $(function() {
        $('#poliza_download_btn').on('click', function() {
            let order_id = $("input[name='order_id']").val();
            var route= '/report/pdf/web_sale_extended.report_customreport_customeasytek_template/'
            var url = route + order_id;
            window.location.href = url;
        });
    });
});


odoo.define('web_sale_extended.payment_process', function(require) {
    'use strict';

    if ($('#nav-tab').length) {
        document.getElementById("nav-tab").firstChild.nextSibling.click();
    }

    $(function() {
        $('#credit_card_country_id').selectpicker();
        $('#credit_card_state_id').selectpicker();
        $('#credit_card_city').selectpicker();
        
        $('#pse_country_id').selectpicker();
        $('#pse_state_id').selectpicker('val', '');
        $('#pse_city').selectpicker();
        
        $('#cash_country_id').selectpicker();
        $('#cash_state_id').selectpicker();
        $('#cash_city').selectpicker();
        
        $('#submit_beneficiaries_add').on('click', function() {
            let order_id = $("input[name='order_id']").val();
            let token = $("input[name='token']").val();
            var route = '/my/order/beneficiaries/'
            var url = route + order_id + '?access_token=' + token;
            window.location.href = url;
        });
        
        $('#submit_pse_end_add_beneficiaries').on('click', function() {
            let order_id = $("input[name='order_id']").val();
            let token = $("input[name='token']").val();
            var route = '/my/order/beneficiaries/'
            var url = route + order_id + '?access_token=' + token;
            window.location.href = url;
        });
        
        $('#submit_payment_rejected').on('click', function() {
            var url = '/shop/payment'
            window.location.href = url;
        });
        
        $('#submit_pse_payment_process').on('click', function() {
            var url = '/shop/payment'
            window.location.href = url;
        });
        
        $('#submit_credit_card_end').on('click', function() {
            var url = '/shop/payment'
            window.location.href = url;
        });
        
        $('#submit_pse_end').on('click', function() {
            var url = '/shop/payment'
            window.location.href = url;
        });
        
        $('#submit_payment_cash_success').on('click', function() {
            var url = '/shop'
            window.location.href = url;
        });
        
        function consultarEstadosCreditCard(pais) {
            $.ajax({
                data: { 'id': pais },
                url: "/search/states",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);                    
                    $('#credit_card_state_id').selectpicker('destroy');
                    $('#credit_card_state_id').empty();
                    $('#credit_card_city').selectpicker('destroy');
                    $('#credit_card_city').empty();
                    decode_data.data.states.forEach(function(obj) {
                        $('#credit_card_state_id').append($("<option></option>")
                            .attr("value", obj.state_id).text(obj.state));
                    });
                    let estado = $('#credit_card_state_id').val();
                    let elemento = "select[name='credit_card_city']";
                    consultarCiudadesCreditCard(estado, elemento);
                    $('#credit_card_state_id').selectpicker('render');
                    $('#credit_card_city').selectpicker('render');
                    
                }
            });
        }
        
        
        
        function consultarEstadosCash(pais) {
            $.ajax({
                data: { 'id': pais },
                url: "/search/states",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);                    
                    $('#cash_state_id').selectpicker('destroy');
                    $('#cash_state_id').empty();
                    $('#cash_city').selectpicker('destroy');
                    $('#cash_city').empty();
                    decode_data.data.states.forEach(function(obj) {
                        $('#cash_state_id').append($("<option></option>")
                            .attr("value", obj.state_id).text(obj.state));
                    });
                    let estado = $('#cash_state_id').val();
                    let elemento = "select[name='cash_city']";
                    consultarCiudadesCash(estado, elemento);
                    $('#cash_state_id').selectpicker('render');
                    $('#cash_city').selectpicker('render');
                    
                }
            });
        }
        
        
        
        function consultarEstadosPse(pais) {
            $.ajax({
                data: { 'id': pais },
                url: "/search/states",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);                    
                    $('#pse_state_id').selectpicker('destroy');
                    $('#pse_state_id').empty();
                    $('#pse_city').selectpicker('destroy');
                    $('#pse_city').empty();
                    decode_data.data.states.forEach(function(obj) {
                        $('#pse_state_id').append($("<option></option>")
                            .attr("value", obj.state_id).text(obj.state));
                    });
                    let estado = $('#pse_state_id').val();
                    let elemento = "select[name='pse_city']";
                    consultarCiudadesPSE(estado, elemento);
                    $('#pse_state_id').selectpicker('render');
                    $('#pse_city').selectpicker('render');
                    
                }
            });
        }
        
        
        $('#credit_card_country_id').change(function() {
            let data_select = $("#credit_card_country_id option:selected").val();            
            if (data_select != 49){               
                $('.div_state').hide();
                $('.div_city').hide();
                $('.div_state_text').show();
                $('.div_city_text').show();
            }
            else{ 
                consultarEstadosCreditCard(data_select);                
                $('.div_state_text').hide();
                $('.div_city_text').hide();
                $('.div_state').show();
                $('.div_city').show();   
            }
        });
        
        
        $('#pse_country_id').change(function() {
            let data_select = $("#pse_country_id option:selected").val();            
            if (data_select != 49){               
                $('.div_state').hide();
                $('.div_city').hide();
                $('.div_state_text').show();
                $('.div_city_text').show();
            }
            else{ 
                consultarEstadosCreditCard(data_select);                
                $('.div_state_text').hide();
                $('.div_city_text').hide();
                $('.div_state').show();
                $('.div_city').show();   
            }
        });
        
        $('#cash_country_id').change(function() {
            let data_select = $("#cash_country_id option:selected").val();            
            if (data_select != 49){               
                $('.div_state').hide();
                $('.div_city').hide();
                $('.div_state_text').show();
                $('.div_city_text').show();
            }
            else{ 
                consultarEstadosCreditCard(data_select);                
                $('.div_state_text').hide();
                $('.div_city_text').hide();
                $('.div_state').show();
                $('.div_city').show();   
            }
        });
        
        function consultarZipcodeCreditCard(ciudad){            
            $.ajax({
                data: { 'city_id': ciudad },
                url: "/search/zipcodes",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);
                    document.querySelector("input[name='credit_card_zip']").value = decode_data['data'].zipcode;
                    document.querySelector("input[name='credit_card_zip_id']").value = decode_data['data'].zipid;
                }
            });
        }
        function consultarZipcodePSE(ciudad){
            $.ajax({
                data: { 'city_id': ciudad },
                url: "/search/zipcodes",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);
                    document.querySelector("input[name='pse_zip']").value = decode_data['data'].zipcode;
                    document.querySelector("input[name='pse_zip_id']").value = decode_data['data'].zipid;
                }
            });
        }
        function consultarZipcodeCash(ciudad){
            $.ajax({
                data: { 'city_id': ciudad },
                url: "/search/zipcodes",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);
                    document.querySelector("input[name='cash_zip']").value = decode_data['data'].zipcode;
                    document.querySelector("input[name='cash_zip_id']").value = decode_data['data'].zipid;
                }
            });
        }
        $('#credit_card_city').change(function() {
            let data_select = $("#credit_card_city option:selected").val();
            consultarZipcodeCreditCard(data_select);
        });
        $('#pse_city').change(function() {
            let data_select = $("#pse_city option:selected").val();
            consultarZipcodePSE(data_select);
        });
        $('#cash_city').change(function() {
            let data_select = $("#cash_city option:selected").val();
            consultarZipcodeCash(data_select);
        });
        function consultarCiudadesCreditCard(estado, elemento) {
            $.ajax({
                data: { 'departamento': estado },
                url: "/search/cities",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);
                    let elemento_completo = $(elemento);
                    $('#credit_card_city').selectpicker('destroy');
                    $('#credit_card_city').empty();
                    decode_data.data.cities.forEach(function(obj) {
                        $('#credit_card_city').append($("<option></option>")
                            .attr("value", obj.city_id).text(obj.city));
                    });
                    $("select[name='credit_card_city']").val($("input[name='partner_city_id']").val());
                    $('#credit_card_city').selectpicker();
                    let data_select = $("#credit_card_city option:selected").val();
                    consultarZipcodeCreditCard(data_select);
                }
            });
        }
        function consultarCiudadesPSE(estado, elemento) {
            $.ajax({
                data: { 'departamento': estado },
                url: "/search/cities",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);
                    let elemento_completo = $(elemento);
                    $('#pse_city').selectpicker('destroy');
                    $('#pse_city').empty();
                    decode_data.data.cities.forEach(function(obj) {
                        $('#pse_city').append($("<option></option>")
                            .attr("value", obj.city_id).text(obj.city));
                    });
                    $("select[name='pse_city']").val($("input[name='partner_city_id']").val());
                    $('#pse_city').selectpicker();
                    let data_select = $("#pse_city option:selected").val();
                    consultarZipcodePSE(data_select);
                }
            });
        }
        function consultarCiudadesCash(estado, elemento) {
            $.ajax({
                data: { 'departamento': estado },
                url: "/search/cities",
                type: 'get',
                success: function(data) {
                    let decode_data = JSON.parse(data);
                    let elemento_completo = $(elemento);
                    $('#cash_city').selectpicker('destroy');
                    $('#cash_city').empty();
                    decode_data.data.cities.forEach(function(obj) {
                        $('#cash_city').append($("<option></option>")
                            .attr("value", obj.city_id).text(obj.city));
                    });
                    $("select[name='cash_city']").val($("input[name='partner_city_id']").val());
                    $('#cash_city').selectpicker();
                    let data_select = $("#cash_city option:selected").val();
                    consultarZipcodeCash(data_select);
                }
            });
        }
        
        $("select[name='credit_card_state_id']").on('change', function cambiarEstado() {
            let estado = $(this).val();
            let elemento = "select[name='credit_card_city']";
            if (estado != ''){
                consultarCiudadesCreditCard(estado, elemento);
            } else {
                $('#credit_card_city').selectpicker('destroy');
                $('#credit_card_city').empty();
                $('#credit_card_city').append($("<option></option>")
                            .attr("value", '').text('Ciudad...'));
                $('#credit_card_city').selectpicker();
            }
        });
        $("select[name='pse_state_id']").on('change', function cambiarEstado() {
            let estado = $(this).val();
            let elemento = "select[name='pse_city']";
            if (estado != ''){
                consultarCiudadesPSE(estado, elemento);
            } else {
                $('#pse_city').selectpicker('destroy');
                $('#pse_city').empty();
                $('#pse_city').append($("<option></option>")
                            .attr("value", '').text('Ciudad...'));
                $('#pse_city').selectpicker();
            }
        });
        $("select[name='cash_state_id']").on('change', function cambiarEstado() {
            let estado = $(this).val();
            let elemento = "select[name='cash_city']";
            if (estado != ''){
                consultarCiudadesCash(estado, elemento);
            } else {
                $('#cash_city').selectpicker('destroy');
                $('#cash_city').empty();
                $('#cash_city').append($("<option></option>")
                            .attr("value", '').text('Ciudad...'));
                $('#cash_city').selectpicker();
            }
        });
        
        var partner_country_id = $("input[name='partner_country_id']").val();
        var partner_state_id = $("input[name='partner_state_id']").val();
        var partner_city_id = $("input[name='partner_city_id']").val();

        //$("input[select='partner_country_id'] option:selected").val(partner_country_id);
        $("select[name='credit_card_country_id']").val(partner_country_id);
        $("select[name='credit_card_state_id']").val(partner_state_id);
        $("select[name='credit_card_city']").val(partner_city_id);
        $("select[name='pse_country_id']").val(partner_country_id);
        $("select[name='pse_state_id']").val(partner_state_id);
        $("select[name='pse_city']").val(partner_city_id);
        $("select[name='cash_country_id']").val(partner_country_id);
        $("select[name='cash_state_id']").val(partner_state_id);
        $("select[name='cash_city']").val(partner_city_id);
        $('#credit_card_country_id').selectpicker('refresh')
        $('#credit_card_state_id').selectpicker('refresh')
        $('#credit_card_city').selectpicker('refresh')
        $('#pse_country_id').selectpicker('refresh')
        $('#pse_state_id').selectpicker('refresh')
        $('#pse_city').selectpicker('refresh')
        $('#cash_country_id').selectpicker('refresh')
        $('#cash_state_id').selectpicker('refresh')
        $('#cash_city').selectpicker('refresh')
        
        
        if ($('#partner_document_type').val() == '3') {
            $("select[name='credit_card_partner_type']").val('CC');
            $("select[name='cash_partner_type']").val('CC');
            $("select[name='pse_partner_type']").val('CC');
        } else if ($('#partner_document_type').val() == '7') {
            $("select[name='credit_card_partner_type']").val('PP');
            $("select[name='cash_partner_type']").val('PP');
            $("select[name='pse_partner_type']").val('PP');
        } else if ($('#partner_document_type').val() == '5') {
            $("select[name='credit_card_partner_type']").val('CE');
            $("select[name='cash_partner_type']").val('CE');
            $("select[name='pse_partner_type']").val('CE');
        } else if ($('#partner_document_type').val() == '8') {
            $("select[name='credit_card_partner_type']").val('DE');
            $("select[name='cash_partner_type']").val('DE');
            $("select[name='pse_partner_type']").val('DE');
        }
        
        var credit_city = "select[name='credit_card_city']";
        var pse_city = "select[name='pse_city']";
        var cash_city = "select[name='cash_city']";
        if (partner_state_id){
            consultarCiudadesCreditCard(partner_state_id, credit_city);
            consultarCiudadesPSE(partner_state_id, pse_city);
            consultarCiudadesCash(partner_state_id, cash_city);
        }
       
        $.validator.addMethod("creditCardfechaVencimiento", function (value, element) {
            var lastYear = new Date().getFullYear();
            var lastMonth = new Date.getMonth();
            var selectYear = "select[name='credit_card_due_year']".val();
            var selectMonth = "select[name='credit_card_due_month']".val()
            
            if (lastYear == selectYear){
                if (int(lastMonth) > int(selectMonth)){
                    return false;
                }
            }
            return true;
        }, "Fecha de Vencimiento Invalida");
        
        $.validator.addMethod("lettersnumberonly_creditcard", function(value, element) {
            var document = $("select[name='credit_card_partner_type']").val();
            if (document == 'PP') { //pasaporte
                return this.optional(element) || /^[A-Za-z0-9]*$/g.test(value);
            } else {
                return this.optional(element) || /^[0-9]*$/.test(value);
            }
        }, "deben ser ser solo letras");
        $.validator.addMethod("lettersnumberonly_cash", function(value, element) {
            var document = $("select[name='cash_partner_type']").val();
            if (document == 'PP') { //pasaporte
                return this.optional(element) || /^[A-Za-z0-9]*$/g.test(value);
            } else {
                return this.optional(element) || /^[0-9]*$/.test(value);
            }
        }, "deben ser ser solo letras");
        $.validator.addMethod("lettersnumberonly_pse", function(value, element) {
            var document = $("select[name='pse_partner_type']").val();
            if (document == 'PP') { //pasaporte
                return this.optional(element) || /^[A-Za-z0-9]*$/g.test(value);
            } else {
                return this.optional(element) || /^[0-9]*$/.test(value);
            }
        }, "deben ser ser solo letras");
        $.validator.addMethod("documentrange_credit_card", function(value, element) {
            var document = $("select[name='credit_card_partner_document']").val();
            if (document == 'CC') { //cédula de ciudadanía
                if ($.isNumeric(value) && (value < 69999 || value > 9999999999)) {
                    return false;
                } else {
                    return true;
                }
            }
            return true;
        }, "número de documento invalido");
        $.validator.addMethod("documentrange_cash", function(value, element) {
            var document = $("select[name='cash_partner_document']").val();
            if (document == 'CC') { //cédula de ciudadanía
                if ($.isNumeric(value) && (value < 69999 || value > 9999999999)) {
                    return false;
                } else {
                    return true;
                }
            }
            return true;
        }, "número de documento invalido");
        $.validator.addMethod("documentrange_pse", function(value, element) {
            var document = $("select[name='pse_partner_document']").val();
            if (document == 'CC') { //cédula de ciudadanía
                if ($.isNumeric(value) && (value < 69999 || value > 9999999999)) {
                    return false;
                } else {
                    return true;
                }
            }
            return true;
        }, "número de documento invalido");
        
        $.validator.addMethod("email2", function(value, element) {
            return this.optional(element) || /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/i.test(value);
        }, "deben contener caracteres válidos");


        $("#payulatam-payment-form").validate({
            rules: {
                credit_card_number: {
                    required: true,
                    minlength: 13,
                    maxlength: 16,
                    number: true,
                },
                credit_card_code: {
                    required: true,
                    minlength: 3,
                    maxlength: 4,
                    number: true,
                },
                credit_card_quotes: {
                    required: true,
                },
                credit_card_name: {
                    required: true,
                    minlength: 3,
                    maxlength: 30,
                    lettersonly: true,
                },
                credit_card_billing_firstname: {
                    required: true,
                    lettersonly: true,
                },
                credit_card_billing_lastname: {
                    required: true,
                    lettersonly: true,
                },
                credit_card_billing_email: {
                    required: true,
                    email2: true,
                },
                credit_card_partner_phone: {
                    required: true,                    
                    formMovilFijoLength: true,
                },
                credit_card_partner_document: {
                    required: true,
                    lettersnumberonly_creditcard: true,
                    documentrange_credit_card: true,
                },
                identification_document: {
                    required: true,
                },
                credit_card_partner_street: {
                    required: true,
                    minlength: 3,
                    maxlength: 30,
                    formcomma: true,
                },
                credit_card_city: {
                    required: true,
                },
                credit_card_country_id: {
                    required: true,
                },
                credit_card_state_id: {
                    required: true,
                },
                cash_billing_firstname: {
                    required: true,
                    lettersonly: true,
                },
                cash_card_billing_lastname: {
                    required: true,
                    lettersonly: true,
                },
            },
            messages: {
                credit_card_number: {
                    required: "tu número de tarjeta es requerido",
                    minlength: "debe contener entre 13 y 16 dígitos",
                    maxlength: "debe contener entre 13 y 16 dígitos"
                },
                credit_card_code: {
                    required: "el código de seguridad es requerido",
                    maxlength: "máximo 4 dígitos"
                },
                credit_card_quotes: {
                    required: "seleccione el número de cuotas",
                },
                credit_card_name: {
                    required: "el nombre de tajeta es requerido",
                    minlength: "debe contener 3 o más caracteres",
                    maxlength: "debe contener máximo 30 caracteres",
                    //lettersonly: "debe contener solo letras"
                },
                credit_card_partner_phone: {
                    required: "tu teléfono es requerido",
                    minlength: "debe tener 10 dígitos",
                    maxlength: "debe tener 10 dígitos"

                },
                credit_card_billing_email: {
                    email2: "debe registrar un correo válido",
                },
                credit_card_billing_firstname: {
                    required: "tu(s) nombre(s) es requerido",
                },
                credit_card_billing_lastname: {
                    required: "tu(s) apellido(s) es requerido",
                },
                credit_card_partner_document: {
                    required: "tu número de documento es requerido",
                    lettersnumberonly_creditcard: "solo números (y letras para pasaporte)",
                    documentrange_caredit_card: "número de documento invalido",
                },
                identification_document: {
                    required: "tu número de documento es requerido",
                },
                credit_card_partner_street: {
                    required: "tu dirección es requerida",
                    minlength: "una dirección contiene más de 3 caracteres",
                    maxlength: "tu dirección no puede tener más de 30 caracteres",
                },
                credit_card_city: {
                    required: "tu ciudad es requerida",
                },
                credit_card_country_id: {
                    required: "tu país es requerido",
                },
                credit_card_state_id: {
                    required: "tu departamento es requerido",
                },
                cash_billing_firstname: {
                    required: "tu(s) nombre(s) es requerido",
                },
                cash_billing_lastname: {
                    required: "tu(s) apellido(s) es requerido",
                },
            }
        });

        $("#payulatam-payment-form-cash").validate({
            rules: {
                cash_bank: {
                    required: true,
                },
                cash_billing_firstname: {
                    required: true,
                    lettersonly: true,
                },
                cash_billing_lastname: {
                    required: true,
                    lettersonly: true,
                },
                cash_partner_document: {
                    required: true,
                    lettersnumberonly_cash: true,
                    documentrange_cash: true,
                },
                cash_billing_email: {
                    required: true,
                    email2: true,
                },
                cash_partner_phone: {
                    required: true,                    
                    formMovilFijoLength: true,
                },
                cash_partner_street: {
                    required: true,
                    minlength: 3,
                    maxlength: 30,
                    formcomma: true,
                },
                cash_country_id: {
                    required: true,
                },
                cash_state_id: {
                    required: true,
                },
                cash_city: {
                    required: true,
                },
            },
            messages: {
                cash_bank: {
                    required: "debe seleccionar un medio de pago Efectivo"
                },
                cash_billing_firstname: {
                    required: "tu(s) nombre(s) es requerido",
                    lettersonly: "debe contener solo letras"
                },
                cash_billing_lastname: {
                    required: "tu(s) apellido(s) es requerido",
                    lettersonly: "debe contener solo letras"
                },
                cash_partner_document: {
                    required: "tu No. de documento es requerido",
                    lettersnumberonly_cash: "solo números (y letras para pasaporte)",
                    documentrange_cash: "número de documento invalido",
                },
                cash_billing_email: {
                    required: "tu email es requerido",
                    email2: "debe contener un correo válido"
                },
                cash_partner_phone: {
                    required: "tu teléfono es requerido",
                },
                cash_partner_street: {
                    required: "tu documento es requerido",
                    minlength: "una dirección contiene más de 3 caracteres",
                    maxlength: "tu dirección no puede tener más de 30 caracteres",
                },
                cash_country_id: {
                    required: "debes seleccionar un país",
                },
                cash_state_id: {
                    required: "debes seleccionar un departamento",
                },
                cash_city: {
                    required: "debes seleccionar una ciudad",
                },
            }
        });
        

        $("#payulatam-payment-form-pse").validate({
            rules: {
                pse_bank: {
                    required: true,
                },
                pse_owner: {
                    required: true,
                    lettersonly: true,
                },
                pse_billing_firstname: {
                    required: true,
                    lettersonly: true,
                },
                pse_billing_lastname: {
                    required: true,
                    lettersonly: true,
                },
                pse_partner_document: {
                    required: true,
                    lettersnumberonly_pse: true,
                    documentrange_pse: true,
                },
                pse_billing_partner_document: {
                    required: true,
                    lettersnumberonly_pse: true,
                    documentrange_pse: true,
                },
                pse_billing_email: {
                    required: true,
                    email2: true,
                },
                pse_partner_street: {
                    required: true,
                    minlength: 3,
                    maxlength: 30,
                    formcomma: true,
                },
                pse_partner_phone: {
                    required: true,
                    formMovilFijoLength: true,
                },
                pse_country_id: {
                    required: true,
                },
                pse_state_id: {
                    required: true,
                },
                pse_city: {
                    required: true,
                },
            },
            messages: {
                pse_bank: {
                    required: "el banco es requerido",
                },
                pse_owner: {
                    required: "el titular de la cuenta es requerido",
                    lettersonly: "debe contener solo letras"
                },
                pse_billing_firstname: {
                    required: "tu(s) nombre(s) es requerido",
                    lettersonly: "debe contener solo letras"
                },
                pse_billing_lastname: {
                    required: "tu(s) apellido(s) es requerido",
                    lettersonly: "debe contener solo letras"
                },
                pse_partner_document: {
                    required: "tu No. de documento es requerido",
                    lettersnumberonly_pse: "solo números (y letras para pasaporte)",
                    documentrange_pse: "número de documento invalido",
                },
                pse_billing_partner_document: {
                    required: "tu No. de documento es requerido",
                    lettersnumberonly_pse: "solo números (y letras para pasaporte)",
                    documentrange_pse: "número de documento invalido",
                },
                pse_billing_email: {
                    required: "tu email es requerido",
                    email2: "debe contener un correo válido"
                },
                pse_partner_street: {
                    required: "tu documento es requerido",
                    minlength: "una dirección contiene más de 3 caracteres",
                    maxlength: "tu dirección no puede tener más de 30 caracteres",
                },
                pse_partner_phone: {
                    required: "tu teléfono es requerido",
                },
                pse_country_id: {
                    required: "debes seleccionar un país",
                },
                pse_state_id: {
                    required: "debes seleccionar un departamento",
                },
                pse_city: {
                    required: "debes seleccionar una ciudad",
                },
            }
        });
        
        var bank_url = $("#bank_url").val();
        var url_payment_receipt_pdf = $("#url_payment_receipt_pdf").val();
        var url_payment_receipt_html = $("#url_payment_receipt_html").val();
        if (bank_url) {
            window.open(bank_url);
        }
        if (url_payment_receipt_html) {
            window.open(url_payment_receipt_html);
        }
        if (url_payment_receipt_pdf) {
            window.open(url_payment_receipt_pdf);
        }
    });
    
    $(".submit_payment").on('click', function(e){
        e.preventDefault();
        if($("#payulatam-payment-form").is(":visible")){
            if($("#payulatam-payment-form").valid()){
                $(this).html('<div><p class="preloader"/><span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" />Cargando...</div>');
                $(this).prop('disabled', true);
                $("#payulatam-payment-form").submit();                
            }
        }
        else if ($("#payulatam-payment-form-cash").is(":visible")){
            if($("#payulatam-payment-form-cash").valid()){
                $(this).html('<div><p class="preloader"/><span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" />Cargando...</div>');
                $(this).prop('disabled', true);
                $("#payulatam-payment-form-cash").submit();                
            }
        }
        else if ($("#payulatam-payment-form-pse").is(":visible")){
            if($("#payulatam-payment-form-pse").valid()){
                $(this).html('<div><p class="preloader"/><span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" />Cargando...</div>');
                $(this).prop('disabled', true);
                $("#payulatam-payment-form-pse").submit();                
            }
        }
    });   
});