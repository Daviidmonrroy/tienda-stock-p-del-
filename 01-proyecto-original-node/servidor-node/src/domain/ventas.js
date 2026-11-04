import { ErrorDeDominio } from './errores.js';
import { esEntero } from './dinero.js';
import { validarPrecio } from './precios.js';
import { comisionCentavos } from './comision.js';

const MEDIOS = ['efectivo', 'transferencia', 'fiado'];

/**
 * Valida una venta y devuelve lo que hay que guardar. No toca la base de datos.
 * contexto: { variantes: Map(id->variante), stockDe(varianteId)->número, comisionBp, vendedorId|null }
 */
export function prepararVenta(entrada, contexto) {
  const { items, medioPago, clienteId = null } = entrada;
  if (!Array.isArray(items) || items.length === 0)
    throw new ErrorDeDominio('SIN_ITEMS', 'La venta no tiene productos.');
  if (!MEDIOS.includes(medioPago))
    throw new ErrorDeDominio('MEDIO_INVALIDO', 'Medio de pago inválido.');

  const pedido = new Map();
  const lineas = items.map((it) => {
    const variante = contexto.variantes.get(it.varianteId);
    if (!variante) throw new ErrorDeDominio('VARIANTE_INEXISTENTE', 'Producto inexistente.', 404);
    if (!esEntero(it.cantidad) || it.cantidad <= 0)
      throw new ErrorDeDominio('CANTIDAD_INVALIDA', 'Cantidad inválida.');
    validarPrecio(variante, it.precioUnit);
    pedido.set(variante.id, (pedido.get(variante.id) ?? 0) + it.cantidad);
    const subtotal = it.cantidad * it.precioUnit;
    return {
      varianteId: variante.id,
      cantidad: it.cantidad,
      precioUnit: it.precioUnit,
      precioMinimoSnapshot: variante.precioMinimo,
      costoSnapshot: variante.costo,
      comision: contexto.vendedorId ? comisionCentavos(subtotal, contexto.comisionBp) : 0,
      subtotal,
    };
  });

  for (const [id, cant] of pedido) {
    if (contexto.stockDe(id) < cant)
      throw new ErrorDeDominio('SIN_STOCK', `No hay stock suficiente (${contexto.variantes.get(id).sku}).`, 409);
  }

  const total = lineas.reduce((a, l) => a + l.subtotal, 0);
  let pagado = total;
  if (medioPago === 'fiado') {
    if (!clienteId) throw new ErrorDeDominio('FIADO_SIN_CLIENTE', 'Para fiar hay que elegir un cliente.');
    pagado = entrada.pagado ?? 0;
    if (!esEntero(pagado) || pagado < 0 || pagado > total)
      throw new ErrorDeDominio('PAGO_INVALIDO', 'El pago inicial no es válido.');
  }

  return { total, pagado, saldo: total - pagado, lineas };
}
