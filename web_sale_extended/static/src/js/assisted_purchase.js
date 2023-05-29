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
    const valores = window.location.search;
    if ('?send_email=1' == valores || '?send_email_account_registration_Bancolombia=1' == valores){
        $('#btn_email').prop("disabled",true);   
        $('#response_email').show();
        alert('El correo ha sido enviado');
    }
});