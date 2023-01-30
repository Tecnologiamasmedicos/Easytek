odoo.define('web_sale_extended.beneficiaries_bancolombia', function (require) {
    "use strict";
    require('web.dom_ready');
    let ap = document.getElementById("primary_insured");
    ap.style.maxHeight = ap.scrollHeight + 200 + "px";
    function mostrar(){
        let coll = document.getElementsByClassName("collapsible");
        let i;
        for (i = 0; i < coll.length; i++) {
            coll[i].addEventListener("click", function() {
                this.classList.toggle("active");
                let content = this.nextElementSibling;
                if (content.style.maxHeight){
                    content.style.maxHeight = null;
                } else {
                    content.style.maxHeight = content.scrollHeight + 200 + "px";
                } 
            });
        }
    }
    mostrar();

    function consultarCiudadesBeneficiary(estado, elemento, item) {
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

    $("#add_beneficiaries").one("click", function(event){
        $(this).removeClass("btn_principal").addClass("btn_secundario");
        $('#submit_beneficiaries').removeClass("btn_secundario").addClass("btn_principal");
    })

    $("#add_beneficiaries").on('click', function(e){
        if ($("#beneficiary").valid()){
            let forms = document.getElementsByClassName("collapsible");
            for (let i = 0; i < forms.length; i++) {
                forms[i].classList.toggle("active");
                forms[i].nextElementSibling.style.maxHeight = null;
            }
            mostrar();
            let beneficiaries_number = parseInt($('#beneficiaries_number').val());
            let last_beneficiary = $('#beneficiaries_container a:last').text().split(" ").at(-1);
            if (last_beneficiary === ""){
                last_beneficiary = 0;
            }
            else{
                last_beneficiary = parseInt(last_beneficiary);
            }
            if (last_beneficiary < beneficiaries_number){
                $("input[name='beneficiario']").val(last_beneficiary + 1);
                let objTo = document.getElementById('beneficiaries_container');
                let formPetSpace = document.createElement("div");
                formPetSpace.innerHTML = '\
                <br/>\
                <a class="btn btn-dark btn-lg btn-block collapsible active"><img src="/web_sale_extended/static/src/images/user_bancol.svg" width="25" style="padding-bottom: 5px;"/> Datos del beneficiario ' + (last_beneficiary + 1) + '</a>\
                <div class="content">\
                    <br/>\
                    <div class="form-check">\
                        <input class="form-check-input" type="checkbox" value="0" id="bfCheckBox' + (last_beneficiary + 1) + '" name="bfCheckBox' + (last_beneficiary + 1) + '"/>\
                        <label class="form-check-label" for="bfCheckBox' + (last_beneficiary + 1) + '">\
                            ¿Vive conmigo?\
                        </label>\
                    </div>\
                    <div class="row">\
                        <div class="col-lg-3">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfirstname' + (last_beneficiary + 1) + '">Primer nombre*</label>\
                                <input class="form-control" type="text" name="bfirstname' + (last_beneficiary + 1) + '" />\
                            </div>\
                        </div>\
                        <div class="col-lg-3">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfothername' + (last_beneficiary + 1) + '">Segundo nombre</label>\
                                <input class="form-control" type="text" name="bfothername' + (last_beneficiary + 1) + '" />\
                            </div>\
                        </div>\
                        <div class="col-lg-3">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bflastname' + (last_beneficiary + 1) + '">Primer apellido*</label>\
                                <input class="form-control" type="text" name="bflastname' + (last_beneficiary + 1) + '" />\
                            </div>\
                        </div>\
                        <div class="col-lg-3">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bflastname' + (last_beneficiary + 1) + '2">Segundo apellido</label>\
                                <input class="form-control" type="text" name="bflastname' + (last_beneficiary + 1) + '2" />\
                            </div>\
                        </div>\
                    </div>\
                    <div class="row">\
                        <div class="col-lg-3">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfparentesco' + (last_beneficiary + 1) + '">Parentesco*</label>\
                                <select name="bfparentesco' + (last_beneficiary + 1) + '" class="form-control">\
                                    <option value="">...</option>\
                                    <option value="C" style="">Cónyuge</option>\
                                    <option value="D" style="">Padres</option>\
                                    <option value="H" style="">Hijos</option>\
                                    <option value="M" style="">Hermanos</option>\
                                    <option value="S" style="">Suegros</option>\
                                </select>\
                            </div>\
                        </div>\
                        <div class="col-lg-3">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfdocument' + (last_beneficiary + 1) + '">Tipo de documento*</label>\
                                <select name="bfdocument' + (last_beneficiary + 1) + '" class="form-control">\
                                    <option value="">...</option>\
                                    <option value="16">Carné diplomático</option>\
                                    <option value="3">Cédula de Ciudadanía </option>\
                                    <option value="5">Cédula de Extranjería</option>\
                                    <option value="7">Pasaporte</option>\
                                    <option value="1">Registro Civil de Nacimiento</option>\
                                    <option value="2">Tarjeta de Identidad</option>\
                                </select>\
                            </div>\
                        </div>\
                        <div class="col-lg-3">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfnumero_documento' + (last_beneficiary + 1) + '">Número documento*</label>\
                                <input class="form-control" type="text" name="bfnumero_documento' + (last_beneficiary + 1) + '" />\
                            </div>\
                        </div>\
                        <div class="col-lg-3">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfdate' + (last_beneficiary + 1) + '">Fecha nacimiento*</label>\
                                <input class="form-control" type="date" name="bfdate' + (last_beneficiary + 1) + '"  />\
                            </div>\
                        </div>\
                    </div>\
                    <div class="row">\
                        <div class="col-lg-6">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfaddress' + (last_beneficiary + 1) + '">Dirección de residencia</label>\
                                <input class="form-control" type="text" name="bfaddress' + (last_beneficiary + 1) + '" placeholder="Dirección de residencia"/>\
                            </div>\
                        </div>\
                        <div class="col-lg-3">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfemail' + (last_beneficiary + 1) + '">Email</label>\
                                <input class="form-control" type="email"  name="bfemail' + (last_beneficiary + 1) + '" placeholder="ejemplo@ejemplo.com" />\
                            </div>\
                        </div>\
                        <div class="col-lg-3">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfphone' + (last_beneficiary + 1) + '">Teléfono móvil*</label>\
                                <input class="form-control" type="text" name="bfphone' + (last_beneficiary + 1) + '"/>\
                            </div>\
                        </div>\
                    </div>\
                    <div class="row">\
                        <div class="col-lg-4">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfcountry_id' + (last_beneficiary + 1) + '">País*</label>\
                                <select name="bfcountry_id' + (last_beneficiary + 1) + '" class="form-control">\
                                <option value="49">Colombia</option>\
                                </select>\
                            </div>\
                        </div>\
                        <div class="col-lg-4">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfdeparment' + (last_beneficiary + 1) + '">Departamento*</label>\
                                <select name="bfdeparment' + (last_beneficiary + 1) + '" class="form-control">\
                                    <option value="1384">Antioquia</option>\
                                    <option value="1385">Atlántico</option>\
                                    <option value="1386" selected="True">Bogotá, D.C.</option>\
                                    <option value="1387">Bolívar</option>\
                                    <option value="1388">Boyacá</option>\
                                    <option value="1389">Caldas</option>\
                                    <option value="1390">Caquetá</option>\
                                    <option value="1391">Cauca</option>\
                                    <option value="1392">Cesar</option>\
                                    <option value="1393">Córdoba</option>\
                                    <option value="1394">Cundinamarca</option>\
                                    <option value="1395">Chocó</option>\
                                    <option value="1396">Huila</option>\
                                    <option value="1397">La Guajira</option>\
                                    <option value="1398">Magdalena</option>\
                                    <option value="1399">Meta</option>\
                                    <option value="1400">Nariño</option>\
                                    <option value="1401">Norte De Santander</option>\
                                    <option value="1402">Quindio</option>\
                                    <option value="1403">Risaralda</option>\
                                    <option value="1404">Santander</option>\
                                    <option value="1405">Sucre</option>\
                                    <option value="1406">Tolima</option>\
                                    <option value="1407">Valle Del Cauca</option>\
                                    <option value="1408">Arauca</option>\
                                    <option value="1409">Casanare</option>\
                                    <option value="1410">Putumayo</option>\
                                    <option value="1411">Archipiélago De San Andrés, Providencia Y Santa Catalina</option>\
                                    <option value="1412">Amazonas</option>\
                                    <option value="1413">Guainía</option>\
                                    <option value="1414">Guaviare</option>\
                                    <option value="1415">Vaupés</option>\
                                    <option value="1416">Vichada</option>\
                                </select>\
                            </div>\
                        </div>\
                        <div class="col-lg-4">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfcity' + (last_beneficiary + 1) + '">Ciudad*</label>\
                                <select name="bfcity' + (last_beneficiary + 1) + '" id="bfcity' + (last_beneficiary + 1) + '" class="form-control">\
                                    <option value="1282">Bogota</option>\
                                </select>\
                            </div>\
                        </div>\
                    </div>\
                    <div class="row">\
                        <div class="col-lg-4">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfsex' + (last_beneficiary + 1) + '">Sexo*</label>\
                                <select name="bfsex' + (last_beneficiary + 1) + '" class="form-control">\
                                    <option value="">Seleccione...</option>\
                                    <option value="M">Masculino</option>\
                                    <option value="F" style="">Femenino</option>\
                                </select>\
                            </div>\
                        </div>\
                        <div class="col-lg-4">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bfocupacion' + (last_beneficiary + 1) + '">Ocupación</label>\
                                <input class="form-control" type="text" name="bfocupacion' + (last_beneficiary + 1) + '"  />\
                            </div>\
                        </div>\
                        <div class="col-lg-4">\
                            <div class="form-group">\
                                <label class="col-form-label" for="bffijo' + (last_beneficiary + 1) + '">Teléfono fijo</label>\
                                <input class="form-control" type="text" name="bffijo' + (last_beneficiary + 1) + '" />\
                            </div>\
                        </div>\
                    </div>\
                </div>\
                ';
                objTo.appendChild(formPetSpace);
                mostrar();
                let forms = document.getElementsByClassName("collapsible");
                forms[forms.length - 1].nextElementSibling.style.maxHeight = forms[forms.length - 1].nextElementSibling.scrollHeight + 200 + "px";
                if (!$("#del_beneficiaries").is(":visible")){
                    $("#del_beneficiaries").show();
                }
            }
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
        }
    });

    $("#del_beneficiaries").on('click', function(e){
        $("input[name='beneficiario']").val($("input[name='beneficiario']").val() - 1);
        let beneficiaries_container = document.getElementById("beneficiaries_container");
        beneficiaries_container.removeChild(beneficiaries_container.childNodes[beneficiaries_container.childNodes.length-1]);
        let forms = document.getElementsByClassName("collapsible");
        forms[forms.length - 1].nextElementSibling.style.maxHeight = forms[forms.length - 1].nextElementSibling.scrollHeight + 200 + "px";
        forms[forms.length - 1].classList.toggle("active");
        if (beneficiaries_container.childNodes.length === 0){
            $(this).hide();
        }
    });
    
    if($("#add_beneficiaries").is(":visible") === true){
        $("#add_beneficiaries").addClass("btn_principal");
        $("#submit_beneficiaries").removeClass("btn_principal").addClass("btn_secundario");
    }
});