odoo.define('web_sale_extended.show_website_cities', function(require) {
    'use strict';
    var ajax = require('web.ajax');
    var core = require('web.core');
    var sAnimation = require('website.content.snippets.animation');

    var qweb = core.qweb;
    var _t = core._t;
    var ajax = require('web.ajax');
    var dest = 0;

    sAnimation.registry.OdooWebsiteSearchCity = sAnimation.Class.extend({
        selector: ".search-query-city",
        autocompleteMinWidth: 300,
        init: function() {
            console.log('init: search_city');
        },
        start: function() {
            var self = this;

            this.$target.attr("autocomplete", "off");
            this.$target.parent().addClass("typeahead__container");
            this.$target.typeahead({
                minLength: 1,
                maxItem: 15,
                delay: 500,
                order: "asc",
                cache: false,
                hint: true,
                accent: true,
                //           autofocus: true,
                //mustSelectItem: true,
                //item: 5334,
                //display: ["id","city"],
                display: ["city"],
                template: '<span>' +
                    '<span>{{city}}</span>' +
                    '</span>',
                source: { city: { url: [{ type: "GET", url: "/search/suggestion_city", data: { query: "{{query}}" }, }, "data.cities"] }, },
                callback: {
                    onClickAfter: function(node, a, item, event) {
                        console.log("CLICK");
                    }
                }
            });
        },
        debug: true,
    });





});