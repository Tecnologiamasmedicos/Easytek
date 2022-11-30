odoo.define('web_sale_extended.beneficiaries_bancolombia', function (require) {
    "use strict";
    require('web.dom_ready');
    function mostrar(){
        var coll = document.getElementsByClassName("collapsible");
        var i;
        for (i = 0; i < coll.length; i++) {
            coll[i].addEventListener("click", function() {
                this.classList.toggle("active");
                var content = this.nextElementSibling;
                if (content.style.maxHeight){
                content.style.maxHeight = null;
                } else {
                content.style.maxHeight = content.scrollHeight + "px";
                } 
            });
        }
    }
    mostrar();
    $("#add_beneficiaries").on('click', function(e){
        let beneficiaries_number = parseInt($('#beneficiaries_number').val());
        let last_beneficiary = $('#beneficiaries_container a:last').text().split(" ").at(-1);
        if (last_beneficiary === "Principal"){
            last_beneficiary = 0;
        }
        else{
            last_beneficiary = parseInt(last_beneficiary);
        }
        if (last_beneficiary < beneficiaries_number){
            let objTo = document.getElementById('beneficiaries_container');
            let formPetSpace = document.createElement("div");
            formPetSpace.innerHTML = '\
            <br/>\
            <a class="btn btn-dark btn-lg btn-block collapsible"><i class="fa-solid fa-user"/> Datos del beneficiario ' + (last_beneficiary + 1) + '</a>\
            <div class="content">\
                <div class="form-check">\
                    <input class="form-check-input" type="checkbox" value="0" id="bfCheckBox' + (last_beneficiary + 1) + '" name="bfCheckBox' + (last_beneficiary + 1) + '"/>\
                    <label class="form-check-label" for="bfCheckBox' + (last_beneficiary + 1) + '">\
                        ¿Vive conmigo?\
                    </label>\
                </div>\
                <div class="row">\
                    <div class="col-lg-3">\
                        <div class="form-group">\
                            <label class="col-form-label" for="bfirstname' + (last_beneficiary + 1) + '">Primer Nombre*</label>\
                            <input class="form-control" type="text" name="bfirstname' + (last_beneficiary + 1) + '" />\
                        </div>\
                    </div>\
                    <div class="col-lg-3">\
                        <div class="form-group">\
                            <label class="col-form-label" for="bfothername' + (last_beneficiary + 1) + '">Segundo Nombre</label>\
                            <input class="form-control" type="text" name="bfothername' + (last_beneficiary + 1) + '" />\
                        </div>\
                    </div>\
                    <div class="col-lg-3">\
                        <div class="form-group">\
                            <label class="col-form-label" for="bflastname' + (last_beneficiary + 1) + '">Primer Apellido*</label>\
                            <input class="form-control" type="text" name="bflastname' + (last_beneficiary + 1) + '" />\
                        </div>\
                    </div>\
                    <div class="col-lg-3">\
                        <div class="form-group">\
                            <label class="col-form-label" for="bflastname' + (last_beneficiary + 1) + '2">Segundo Apellido</label>\
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
                                <t t-foreach="document_types" t-as="dt">\
                                    <option t-att-value="dt.id">\
                                        <t t-esc="dt.name" />\
                                    </option>\
                                </t>\
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
                            <label class="col-form-label" for="bfphone' + (last_beneficiary + 1) + '">Teléfono Móvil*</label>\
                            <input class="form-control" type="text" name="bfphone' + (last_beneficiary + 1) + '"/>\
                        </div>\
                    </div>\
                </div>\
                <div class="row">\
                    <div class="col-lg-4">\
                        <div class="form-group">\
                            <label class="col-form-label" for="bfcountry_id' + (last_beneficiary + 1) + '">País*</label>\
                            <select name="bfcountry_id' + (last_beneficiary + 1) + '" class="form-control">\
                                <t t-foreach="countries" t-as="c">\
                                    <option t-att-value="c.id" t-att-selected="c.id == (country and country.id)">\
                                        <t t-esc="c.name" />\
                                    </option>\
                                    </t>\
                            </select>\
                        </div>\
                    </div>\
                    <div class="col-lg-4">\
                        <div class="form-group">\
                            <label class="col-form-label" for="bfdeparment' + (last_beneficiary + 1) + '">Departamento*</label>\
                            <select name="bfdeparment' + (last_beneficiary + 1) + '" class="form-control">\
                                <t t-foreach="country_states" t-as="s">\
                                    <option t-att-value="s.id" t-att-selected="s.id == 1386">\
                                        <t t-esc="s.name" />\
                                    </option>\
                                </t>\
                            </select>\
                        </div>\
                    </div>\
                    <div class="col-lg-4">\
                        <div class="form-group">\
                            <label class="col-form-label" for="bfcity' + (last_beneficiary + 1) + '">Ciudad*</label>\
                            <select name="bfcity' + (last_beneficiary + 1) + '" id="bfcity' + (last_beneficiary + 1) + '" class="form-control">\
                                <t t-foreach="cities" t-as="c">\
                                    <option t-att-value="c.city_id.id">\
                                        <t t-esc="c.city_id.name" />\
                                    </option>\
                                </t>\
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
        }
    });
});