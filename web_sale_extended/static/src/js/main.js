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
            console.log(data_select);
            let array_data = data_select.split(" ");
            console.log(array_data[60]);
            document.querySelector("input[name='zip']").value = array_data[60]
        });


    });
    $("#beneficiary1").hide();
    $("#beneficiary2").hide();
    $("#beneficiary3").hide();
    $("#beneficiary4").hide();
    $("#beneficiary5").hide();
    $("#beneficiary6").hide();

    document.getElementById('cant_beneficiarios').addEventListener('change', function() {
        let cantidad_beneficiarios = parseInt(this.value);
        for (let index = 0; index < cantidad_beneficiarios; index++) {
            let id_elemento = "#beneficiary" + (index + 1);
            $(id_elemento).show();

        }
    });
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