odoo.define('web_sale_extended.show_website_cities', function(require) {
    'use strict';

    $(function() {
        console.log("ready");
        $('#country_id').selectpicker();
        $('#state_id').selectpicker();
        $('#city').selectpicker();
        $('#document').selectpicker();
        $('#fiscal_position').selectpicker();

        $('#city').change(function() {
            let data_select = $("#city option:selected").text();
            let array_data = data_select.split(' ');
            console.log("split");
            console.log(array_data);
            document.querySelector("input[name='zip']").value = array_data[52]
        });
        $("input[name='bfdate1']").on('change', function calcularEdad() {
            let fecha = $(this).val();
            console.log(fecha);

            let hoy = new Date();
            let cumpleanos = new Date(fecha);
            let edad = hoy.getFullYear() - cumpleanos.getFullYear();
            let m = hoy.getMonth() - cumpleanos.getMonth();
            if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
                edad--;
            }
            let email_asegurador = $("input[name='email']").val();
            let telefono_fijo_asegurador = $("input[name='fijo']").val();
            let ciudad_asegurador = $("input[name='city']").val();
            let adress_asegurador = $("input[name='address']").val();
            let asegurador_state = $("input[name='deparment']").val();
            let country_asegurador = $("input[name='country_id']").val();
            if (edad < 18) {
                console.log("Eres menor de edad perro");

                $("input[name='bfemail1']").val(email_asegurador);
                $("input[name='bfaddress1']").val(adress_asegurador);
                //$("select[name='bfcountry_id1']").val(country_asegurador);
                //$("select[name='bfdeparment1']").val(asegurador_state);
                //$("select[name='bfcity1']").val(ciudad_asegurador);
                $("input[name='bffijo1']").val(telefono_fijo_asegurador);

            }
        });
        $("#terminos").hide();
        $("#politica").hide();
        $("#shop").validate({
            rules: {
                name: {
                    required: true,
                    minlength: 3
                },
                lastname: {
                    required: true,
                    minlength: 3
                },
                lastname2: {
                    required: true,
                    minlength: 3
                },
                email: {
                    required: true,
                    email: true

                },
                phone: {
                    required: true,


                },
                document: {
                    required: true
                },
                identification_document: {
                    required: true,
                    number: true,

                },

                street: {
                    required: true,
                },
                city: {
                    required: true,

                },
                country_id: {
                    required: true,

                },
                state_id: {
                    required: true,
                },
                aceptacion_datos: {
                    required: true
                },
                tyc: {
                    required: true
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


                            return edad > 69
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


            },
            messages: {
                name: {
                    required: "Upss!! tu nombre es requerido",
                    minlength: "Un nombre contiene más de 3 caracteres"
                },
                lastname: {
                    required: "Este campo es requerido",
                    minlength: "Un apellido contiene más de 3 caracteres"
                },
                lastname2: {
                    required: "Este campo es requerido",
                    minlength: "Un apellido contiene más de 3 caracteres"
                },
                email: {
                    required: "Este campo es requerido",
                    email: "Escribe un email valido"
                },
                phone: {
                    required: "Este campo es requerido",

                },
                document: {
                    required: "Este campo es requerido",

                },
                identification_document: {
                    required: "Este campo es requerido",
                    number: "Este campo solo es numérico"

                },
                street: {
                    required: "Este campo es requerido",

                },
                city: {
                    required: "Este campo es requerido",

                },
                country_id: {
                    required: "Este campo es requerido",

                },
                state_id: {
                    required: "Este campo es requerido",

                },
                aceptacion_datos: {
                    required: "Upss Acepte política de tratamiento de datos para continuar",

                },
                tyc: {
                    required: "Acepte terminos y condiciones para continuar",

                },
                birthdate_date: {
                    required: "Campo de fecha es obligatorio",
                    min: "Tienes que ser mayor de edad",
                    max: "Ups debes de ser mayor 18 y menor de 69 años para continuar"

                },

            }
        });

        hide_beneficiaries();


    });


    function hide_beneficiaries() {
        $("#beneficiary1").hide();
        $("#beneficiary2").hide();
        $("#beneficiary3").hide();
        $("#beneficiary4").hide();
        $("#beneficiary5").hide();
        $("#beneficiary6").hide();

    }


    $("#cant_beneficiarios").on('change', function mostrarbeneficiarios() {
        let cantidad_beneficiarios = parseInt($(this).val());
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
    });
    $("select[name='estado_civil']").on('change', function cambiarConyugues() {
        console.log("cambio");

        let estado = $(this).val();
        if (estado == 'Soltero') {
            let newOptions = {
                Seleccione: "",
                PADRES: "D",
                HIJOS: "H",
                HERMANOS: "M"
            };
            for (let index = 0; index < 6; index++) {
                let id_elemento = 'bfparentesco' + (index + 1);
                console.log(id_elemento);
                let elemento = "select[name='" + id_elemento + "']";
                console.log(elemento);
                let elemento_completo = $(elemento);
                console.log(elemento_completo);
                elemento_completo.empty();
                $.each(newOptions, function(key, value) {
                    elemento_completo.append($("<option></option>")
                        .attr("value", value).text(key));
                });

            }



        } else if (estado == 'Viudo') {
            let newOptions = {
                Seleccione: "",
                PADRES: "D",
                HIJOS: "H",
                HERMANOS: "M",
                SUEGROS: "S"
            };
            for (let index = 0; index < 6; index++) {
                let id_elemento = 'bfparentesco' + (index + 1);
                console.log(id_elemento);
                let elemento = "select[name='" + id_elemento + "']";
                console.log(elemento);
                let elemento_completo = $(elemento);
                console.log(elemento_completo);
                elemento_completo.empty();
                $.each(newOptions, function(key, value) {
                    elemento_completo.append($("<option></option>")
                        .attr("value", value).text(key));
                });

            }



        } else {
            let newOptions = {
                Seleccione: "",
                CONYUGUE: "C",
                PADRES: "D",
                HIJOS: "H",
                HERMANOS: "M",
                SUEGROS: "S"
            };
            for (let index = 0; index < 6; index++) {
                let id_elemento = 'bfparentesco' + (index + 1);
                console.log(id_elemento);
                let elemento = "select[name='" + id_elemento + "']";
                console.log(elemento);
                let elemento_completo = $(elemento);
                console.log(elemento_completo);
                elemento_completo.empty();
                $.each(newOptions, function(key, value) {
                    elemento_completo.append($("<option></option>")
                        .attr("value", value).text(key));
                });

            }



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
                elemento_completo.empty();
                decode_data.data.cities.forEach(function(obj) {
                    elemento_completo.append($("<option></option>")
                        .attr("value", obj.city).text(obj.city));
                });

            }

        });

    }


    $("select[name='deparment']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[name='city']";
        consultarCiudades(estado, elemento);

    });
    $("select[name='bfdeparment1']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[name='bfcity1']";
        consultarCiudades(estado, elemento);

    });
    $("select[name='bfdeparment2']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[name='bfcity2']";
        consultarCiudades(estado, elemento);

    });
    $("select[name='bfdeparment3']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[name='bfcity3']";
        consultarCiudades(estado, elemento);

    });
    $("select[name='bfdeparment4']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[name='bfcity4']";
        consultarCiudades(estado, elemento);

    });
    $("select[name='bfdeparment5']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[name='bfcity5']";
        consultarCiudades(estado, elemento);

    });
    $("select[name='bfdeparment6']").on('change', function cambiarCiudades() {
        let estado = $(this).val();
        let elemento = "select[name='bfcity6']";
        consultarCiudades(estado, elemento);

    });
    $("#btn_terminos").click(function() {
        $("#politica").hide();
        $("#terminos").show();

    });
    $("#btn_politica").click(function() {
        $("#terminos").hide();
        $("#politica").show();

    });




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