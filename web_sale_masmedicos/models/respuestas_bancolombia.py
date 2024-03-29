respuestas = {
    "C01": "Nit de entidad que envía no es numérico",
    "C02": "Código de Convenio no es numérico",
    "C03": "Fecha de Generación/transmisión de lote con formato inválido",
    "C04": "Secuencia de lote no tiene un valor válido",
    "C06": "Número de registros no es numérico",
    "C07": "Sumatoria de débitos no es numérico ",
    "C08": "Código de Convenio no inscrito en Sistema de Recaudos",
    "C09": "Nit de entidad que envía no inscrito en convenio",
    "C12": "Número de registros enviados no coincide con lo recibido",
    "C13": "Sumatoria de débitos no coincide con lo recibido",
    "C14": "Tipo de registro de control inválido",
    "C15": "Archivo sin registros de detalle/documentos",
    "C16": "Convenio no está activo en el sistema",
    "C90": "Convenio no tiene inscripción en el recaudador o en ambos",
    "C91": "EL tipo de formato del archivo es diferente al seleccionado en pantalla",
    "C92": "Los datos del primer registro del archivo no identifican ningún convenio",
    "C93": "Valor total de los débitos en archivo diferente a valor ingresado en la captura",
    "C94": "Número de registros en archivo diferente a número de registros en captura",
    "C95": "Archivo ya fue aplicado en contingencia hoy.",
    "C96": "Modalidad del convenio no es por demanda o base de datos ",
    "C97": "Nit del archivo no coincide con Nit ingresado en la captura",
    "C98": "Archivo a procesar no pertenece al convenio ingresado en la captura",
    "C99": "Archivo sin Registros",
    "D01": "Tipo de registro de detalle inválido",
    "D02": "Banco de la cuenta a debitar no es numérico",
    "D03": "Cuenta a debitar no es numérica",
    "D04": "Tipo de transacción no es numérico",
    "D05": "Valor de la transacción no es numérico",
    "D06": "Indicador de validación Nit/Cta no es So N",
    "D07": "No existe Nit para validar contra cuenta",
    "D08": "Código de Banco inválido",
    "D09": "Tipo de transacción no existe",
    "D10": "Cuenta a debitar no existe",
    "D11": "Cuenta en Depósitos con estado inválido para efectuar débitos",
    "D12": "Cuenta a debitar no pertenece a Nit",
    "D13": "Tarjeta de crédito no existe",
    "D14": "Cuenta de Tarjeta de crédito con bloqueos para efectuar débitos",
    "D15": "Tarjeta de crédito a debitar no pertenece a Nit",
    "D16": "Registro de documentos no pertenece a ningún registro de detalle",
    "D17": "Código de Banco no existe en ACH",
    "D18": "Banco no autorizado para débitos en ACH",
    "D19": "Validación Nit /Cuenta es requerida para débitos ACH",
    "D20": "Nit del pagador viene en ceros y es requerido para débitos ACH",
    "D21": "Tipo de transacción no válida para débitos en ACH",
    "D22": "Campo de Referencia 1 es requerido para débitos en ACH",
    "D23": "Cuenta a debitar no ha sido prenotificada en ACH",
    "D24": "Cuenta a debitar tiene prenotificación con estado inválido",
    "D25": "Convenio no habilitado para débitos en ACH",
    "D26": "Nit del pagador no es un campo numérico",
    "D27": "Fecha de aplicación o vencimiento con formato inválido ",
    "D28": "Tipo de documento del pagador no válido",
    "D29": "Fecha de aplicación debe ser posterior a fecha actual de proceso en el sistema",
    "D30": "Campo Nombre del Pagador es obligatorio para débitos en ACH",
    "D31": "Valor de transacción no puede venir en cero para Facturación",
    "D32": "Numero de factura inválida",
    "D33": "Días de reintentos no válidos",
    "D34": "Periodo liquidado no es un campo numérico",
    "D35": "Tarjeta vencida",
    "D36": "Criterios para la aplicación no válidos",
    "D37": "Frecuencia de pago no válida",
    "D38": "Número de días no válido",
    "D39": "Día de pago no válido",
    "D41": "Registro pendiente por duplicado",
    "D42": "Registro duplicado",
    "D43": "Fecha inicio de programación es mayor a la fecha de vigencia del convenio",
    "D51": "Disponible no es suficiente para débito total",
    "D52": "Disponible no es suficiente para efectuar débitos parciales",
    "D53": "No está disponible archivo de saldos (error en comunicaciones)",
    "D54": "No se pudo consultar por tiempo excedido (error en comunicaciones )",
    "D55": "Cuenta con saldo negativo",
    "D56": "Error de datos en transacción enviada al TEF",
    "D57": "Transacción rechazada por servidor no disponible",
    "OK0": "Validación sin problemas **(Estado transitorio para débitos Bancolombia)",
    "OK1": "Débito Total Exitoso",
    "OK2": "Débito Parcial Exitoso",
    "OK3": "Débito Pendiente de Respuesta en ACH**(Estado transitorio para débitos ACH)",
    "OK4": "Debito Total Exitoso en entidad ACH",
    "OK5": "Prenotificación aceptada en entidad ACH",
    "R00": "Transacción exitosa",
    "R01": "Fondos insuficientes en entidad ACH",
    "R02": "Cuenta cerrada en entidad ACH ",
    "R03": "Cuenta no abierta en entidad ACH",
    "R04": "Número de cuenta inválido en entidad ACH",
    "R06": "Devolución solicitada por la entidad financiera originadora",
    "R07": "Autorización de recaudo revocada por el cliente receptor",
    "R08": "Orden de no pago",
    "R09": "Fondos no disponibles",
    "R10": "Devolución débito por solicitud del cliente receptor - Persona natural",
    "R12": "Sucursal vendida a otra entidad financiera",
    "R13": "Entidad Financiera Receptora no vinculada al sistema ACH o número de ruta y transito invalido",
    "R14": "Muerte del delegado o representante",
    "R15": "Muerte del beneficiario o titular de la cuenta",
    "R16": "Cuenta inactiva o cuenta bloqueada",
    "R17": "La identificación no coincide con cuenta del cliente receptor",
    "R18": "La fecha efectiva de la transacción es menor a la de proceso.",
    "R19": "Error en el campo valor de la transacción.",
    "R20": "Cuenta no habilitada para recibir transacciones",
    "R26": "Error en campo mandatorio u obligatorio",
    "R27": "Error en el número de secuencia",
    "R28": "Devolución Transacción débito por contingencia",
    "R29": "Devolución de una transacción débito por solicitud del Cliente Receptor (Persona Jurídica): La Entidad Financiera Receptora ha sido notificada por su Cliente Receptor Corporativo (no consumidor), que el Cliente Originador de la transacción no ha sido auto",
    "R30": "Novedad de enrolamiento o retiro no permitido",
    "R31": "La referencia supera la longitud o contiene valores no permitidos",
    "R32": "La entidad financiera Receptora de la transacción no puede efectuar la compensación.",
    "R34": "Participación limitada de la entidad Financiera Receptora de la transacción",
    "R98": "Devolución no definida.",
    "D28": "Tipo de documento del pagador no válido",
    "D33": "Días de reintentos no válidos",
    "D36": "Criterios para la aplicación no válidos",
    "D37": "Frecuencia de pago no válida",
    "D38": "Número de días no válido",
    "D39": "Día de pago no válido",
    "D42": "(Nuevo sistema de Recaudos)	Débito parcial no válido",
    "D43": "Fecha inicio de programación es mayor a la fecha de vigencia del convenio",
    "D44": "Cantidad de días insuficientes entre la fecha de inicio y la siguiente fecha de aplicación",
    "D65": "La inscripción ya se encuentra activa",
    "D63": "La referencia supera la longitud o contiene valores no permitidos",
    "D64": "Tipo de novedad no es válido",
    "D66": "Inscripción a retirar no se encuentra activa",
}
