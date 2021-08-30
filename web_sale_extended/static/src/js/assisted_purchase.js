odoo.define('web_sale_extended.assisted_purchase', function (require) {
"use strict";
    require('web.dom_ready');      
    $('.menu li:has(ul)').click(function (e) {
        if ($(this).hasClass('activado')) {
            $(this).removeClass('activado');
            $(this).children('ul').slideUp();
        }
        else {
            $('.menu li ul').slideUp();
            $('.menu li').removeClass('activado');
            $(this).addClass('activado');
            $(this).children('ul').slideDown();
        }
    }); 
});