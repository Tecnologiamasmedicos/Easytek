# -*- coding: utf-8 -*-
import logging, time, csv, json
from odoo import fields, models, tools, api,_
from datetime import date, timedelta, datetime
from odoo.osv import expression
from odoo.tools import date_utils

import hubspot
from pprint import pprint
from hubspot.crm.contacts import ApiException, PublicObjectSearchRequest, SimplePublicObjectInput

_logger = logging.getLogger(__name__)

    
class hubSpot(models.Model):
    _name = 'api.hubspot'
    
# import hubspot
# from pprint import pprint
# from hubspot.crm.contacts import SimplePublicObjectInput, ApiException

# client = hubspot.Client.create(api_key="YOUR_HUBSPOT_API_KEY")

# properties = {
#     "company": "Biglytics",
#     "email": "bcooper@biglytics.net",
#     "firstname": "Bryan",
#     "lastname": "Cooper",
#     "phone": "(877) 929-0687",
#     "website": "biglytics.net"
# }
# simple_public_object_input = SimplePublicObjectInput(properties=properties)
# try:
#     api_response = client.crm.contacts.basic_api.create(simple_public_object_input=simple_public_object_input)
#     pprint(api_response)
# except ApiException as e:
#     print("Exception when calling basic_api->create: %s\n" % e)
    
    
    
    
    
    
    
    
    
    
    def consulta(self):
        hubspot_api_env = self.env.user.company_id.sftp_server_env
        if hubspot_api_env == 'prod':
            hubspot_api_key = self.env.user.company_id.hubspot_api_key
        else:
            hubspot_api_key = self.env.user.company_id.hubspot_api_key_QA
        client = hubspot.Client.create(api_key=hubspot_api_key)
        
        public_object_search_request = PublicObjectSearchRequest(filter_groups=[{"filters":[{"value":"andresrojas566@gmail.com","propertyName":"email","operator":"EQ"}, {"value":"1019008064","propertyName":"numero_documento","operator":"EQ"}]}], properties=["es_comprador_", "numero_documento"])
        
#         public_object_search_request = PublicObjectSearchRequest(filter_groups=[{"filters":[{"value":"andresrojas566@gmail.com","propertyName":"email","operator":"EQ"}, {"value":"1019008064","propertyName":"numero_documento","operator":"EQ"}]}])
        
        
#         PublicObjectSearchRequest(filter_groups=[{"filters":[{"value":"string","values":["string"],"propertyName":"name","operator":"EQ"}]}], sorts=["string"], query="string", properties=["string"], limit=0, after=0)
        
        try:
#             api_response = client.crm.contacts.basic_api.get_page(limit=10, archived=False)
            api_response = client.crm.contacts.search_api.do_search(public_object_search_request=public_object_search_request)
            _logger.info(api_response)
        
            if len(api_response.results) != 0:
                _logger.info("existe")
                if api_response.results[0].properties['es_comprador_'] != 'SI':
                    properties = {
                        "es_comprador_": "SI",
                        'date_of_birth': datetime.date(1980, 10, 10),
                    }
                    simple_public_object_input = SimplePublicObjectInput(properties=properties)
                    a = api_response.results[0].id
                    api_response2 = client.crm.contacts.basic_api.update(contact_id=a, simple_public_object_input=simple_public_object_input)
                else:
                    _logger.info("Ya tiene el valor si")
                
            else: 
                _logger.info("No existe")
                
                
#             _logger.info(type(api_response))
#             _logger.info(api_response.results)
#             _logger.info(type(api_response.results))
#             _logger.info(api_response.results[0].properties)
#             _logger.info(api_response.results[0].properties.keys())
#             _logger.info(api_response.results[0].properties['es_comprador_'])
            
#             if api_response.results[0].properties['es_comprador_'] == None:
#                 _logger.info("No es")
            
#             _logger.info(json.dumps(api_response))
#             _logger.info(api_response['results']['properties'])
#             _logger.info(type(api_response))
        except ApiException as e:
#             _logger.error("Exception when calling basic_api->get_page: %s\n" % e)
            print("Exception when calling search_api->do_search: %s\n" % e)
    
    
    
    
    def search_country(self, country_id):
        paises = {
            '3': 'Afganistán',
            '6': 'Albania',
            '57': 'Alemania',
            '1': 'Andorra',
            '8': 'Angola',
            '5': 'Anguila',
            '9': 'Antártida',
            '4': 'Antigua y Barbuda',
            '192': 'Arabia Saudita',
            '62': 'Argelia',
            '10': 'Argentina',
            '7': 'Armenia',
            '14': 'Aruba',
            '13': 'Australia',
            '12': 'Austria',
            '16': 'Azerbaiyán',
            '32': 'Bahamas',
            '23': 'Bahrein',
            '19': 'Bangladesh',
            '18': 'Barbados',
            '20': 'Bélgica',
            '37': 'Belice',
            '25': 'Benin',
            '36': 'Bielorrusia',
            '29': 'Bolivia',
            '17': 'Bosnia y Herzegovina',
            '35': 'Botsuana',
            '31': 'Brasil',
            '28': 'Brunei',
            '22': 'Bulgaria',
            '21': 'Burkina Faso',
            '24': 'Burundi',
            '33': 'Bután',
            '52': 'Cabo Verde',
            '116': 'Camboya',
            '47': 'Camerún',
            '38': 'Canadá',
            '214': 'Chad',
            '46': 'Chile',
            '48': 'China',
            '55': 'Chipre',
            '236': 'Ciudad del Vaticano',
            '49': 'Colombia',
            '118': 'Comoras',
            '42': 'Congo',
            '120': 'Corea del Norte',
            '121': 'Corea del Sur',
            '44': 'Costa de Marfil',
            '50': 'Costa Rica',
            '97': 'Croacia',
            '51': 'Cuba',
            '53': 'Curazao',
            '59': 'Dinamarca',
            '58': 'Djibouti',
            '60': 'Dominica',
            '63': 'Ecuador',
            '65': 'Egipto',
            '209': 'El Salvador',
            '2': 'Emiratos Árabes Unidos',
            '67': 'Eritrea',
            '201': 'Eslovaquia',
            '199': 'Eslovenia',
            '68': 'España',
            '233': 'Estados Unidos',
            '64': 'Estonia',
            '69': 'Etiopía',
            '176': 'Filipinas',
            '70': 'Finlandia',
            '71': 'Fiyi',
            '75': 'Francia',
            '76': 'Gabón',
            '84': 'Gambia',
            '78': 'Georgia',
            '89': 'Georgia del sur y las islas Sandwich del sur',
            '80': 'Ghana',
            '81': 'Gibraltar',
            '77': 'Granada',
            '88': 'Grecia',
            '83': 'Groenlandia',
            '86': 'Guadalupe',
            '91': 'Guam',
            '90': 'Guatemala',
            '93': 'Guayana',
            '79': 'Guayana Francesa',
            '82': 'Guernsey',
            '85': 'Guinea',
            '87': 'Guinea Ecuatorial',
            '92': 'Guinea-Bissau',
            '98': 'Haití',
            '96': 'Honduras',
            '94': 'Hong Kong',
            '99': 'Hungría',
            '104': 'India',
            '100': 'Indonesia',
            '106': 'Irak',
            '107': 'Irán',
            '101': 'Irlanda',
            '34': 'Isla Bouvet',
            '54': 'Isla de Navidad',
            '103': 'Isla del hombre',
            '162': 'Isla Norfolk',
            '108': 'Islandia',
            '15': 'Islas Aland',
            '27': 'islas Bermudas',
            '123': 'Islas Caimán',
            '39': 'Islas Cocos (Keeling)',
            '45': 'Islas Cook',
            '74': 'Islas Faroe',
            '95': 'Islas Heard y McDonald',
            '72': 'Islas Malvinas',
            '148': 'Islas Marianas del Norte',
            '142': 'Islas Marshall',
            '232': 'Islas menores alejadas de los Estados Unidos',
            '180': 'Islas Pitcairn',
            '193': 'Islas Salomón',
            '213': 'Islas Turcas y Caicos',
            '239': 'Islas Vírgenes Británicas',
            '240': 'Islas Vírgenes de EE.UU',
            '102': 'Israel',
            '109': 'Italia',
            '111': 'Jamaica',
            '113': 'Japón',
            '110': 'Jersey',
            '112': 'Jordán',
            '186': 'Katar',
            '124': 'Kazajstán',
            '114': 'Kenia',
            '115': 'Kirguizstán',
            '117': 'Kiribati',
            '250': 'Kosovo',
            '122': 'Kuwait',
            '125': 'Laos',
            '131': 'Lesoto',
            '134': 'Letonia',
            '126': 'Líbano',
            '130': 'Liberia',
            '135': 'Libia',
            '128': 'Liechtenstein',
            '132': 'Lituania',
            '133': 'Luxemburgo',
            '147': 'Macau',
            '143': 'Macedonia (ARYM)',
            '141': 'Madagascar',
            '157': 'Malasia',
            '155': 'Malawi',
            '154': 'Maldivas',
            '144': 'Mali',
            '152': 'Malta',
            '136': 'Marruecos',
            '149': 'Martinica',
            '153': 'Mauricio',
            '150': 'Mauritania',
            '246': 'Mayotte',
            '156': 'México',
            '73': 'Micronesia',
            '138': 'Moldavia',
            '137': 'Mónaco',
            '146': 'Mongolia',
            '139': 'Montenegro',
            '151': 'Montserrat',
            '158': 'Mozambique',
            '145': 'Myanmar (Birmania)',
            '159': 'Namibia',
            '168': 'Nauru',
            '167': 'Nepal',
            '164': 'Nicaragua',
            '161': 'Níger',
            '163': 'Nigeria',
            '169': 'Niue',
            '166': 'Noruega',
            '160': 'Nueva Caledonia',
            '170': 'Nueva Zelanda',
            '171': 'Omán',
            '177': 'Pakistán',
            '184': 'Palau',
            '182': 'Palestina',
            '172': 'Panamá',
            '175': 'Papúa Nueva Guinea',
            '185': 'Paraguay',
            '173': 'Perú',
            '174': 'Polinesia Francesa',
            '178': 'Polonia',
            '183': 'Portugal',
            '181': 'Puerto Rico',
            '231': 'Reino Unido',
            '40': 'República Centroafricana',
            '56': 'Republica checa',
            '41': 'República Democrática del Congo',
            '61': 'República Dominicana',
            '187': 'Reunión',
            '191': 'Ruanda',
            '188': 'Rumania',
            '190': 'Rusia',
            '66': 'Sahara Occidental',
            '244': 'Samoa',
            '11': 'Samoa Americana',
            '26': 'San Bartolomé',
            '119': 'San Cristóbal y Nieves',
            '203': 'San Marino',
            '210': 'San Martín',
            '179': 'San Pedro y Miquelón',
            '237': 'San Vicente y las Granadinas',
            '198': 'Santa helena',
            '127': 'Santa Lucía',
            '208': 'Santo Tomé y Príncipe',
            '204': 'Senegal',
            '189': 'Serbia',
            '194': 'Seychelles',
            '202': 'Sierra Leona',
            '197': 'Singapur',
            '211': 'Siria',
            '205': 'Somalia',
            '129': 'Sri Lanka',
            '212': 'Suazilandia',
            '247': 'Sudáfrica',
            '195': 'Sudán',
            '207': 'Sudán del Sur',
            '196': 'Suecia',
            '43': 'Suiza',
            '206': 'Surinam',
            '200': 'Svalbard y Jan Mayen',
            '217': 'Tailandia',
            '227': 'Taiwán',
            '228': 'Tanzania',
            '218': 'Tayikistan',
            '105': 'Territorio Británico del Océano Índico',
            '215': 'Tierras australes y antárticas francesas',
            '223': 'Timor oriental',
            '216': 'Togo',
            '219': 'Tokelau',
            '222': 'Tonga',
            '225': 'Trinidad y Tobago',
            '221': 'Túnez',
            '220': 'Turkmenistan',
            '224': 'Turquía',
            '226': 'Tuvalu',
            '229': 'Ucrania',
            '230': 'Uganda',
            '234': 'Uruguay',
            '235': 'Uzbekistán',
            '242': 'Vanuatu',
            '238': 'Venezuela',
            '241': 'Vietnam',
            '243': 'Wallis y Futuna',
            '245': 'Yemen',
            '248': 'Zambia',
            '249': 'Zimbabue'
        }
        return paises[str(country_id)]
    
    
    def search_document_type(self, document_type_id):
        document_types = {'3': 'CC', '5':'CE', '8':'Documento de Identificación extranjero', '7':'PP'}
        return document_types[str(document_type_id)]
        
    
    
    def create_contact(self, partner):
        
        properties = {
            "firstname": partner.firstname,
            "segundo_nombre": partner.othernames,
            "lastname": str(partner.lastname) + '' + str(partner.lastname2),
            "email": partner.email,
            "phone": partner.mobile if partner.mobile != '' else partner.phone,
            "tipo_de_identificacion": partner.document_type_id,
            "numero_documento": partner.identification_document,
            "date_of_birth": partner.birthdate_date,
            "fecha_de_expedicion_del_documento": partner.expedition_date,
            "address": partner.street,
            "pais2": partner.country_id, #seleccion
            "departamento___estado___provincia": partner.state_id.name, #Texto
            "city": partner.zip_id.city_id.name #Texto
        }
        
        return properties
        
#         try:
#             api_response = client.crm.contacts.basic_api.create(simple_public_object_input=simple_public_object_input)
#             _logger.info(api_response)
#         except ApiException as e:
#             _logger.info("Exception when calling basic_api->create: %s\n" % e)
