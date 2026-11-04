import { ErrorDeDominio } from './errores.js';
import { esEntero } from './dinero.js';

export function validarPrecio(variante, precioCentavos) {
  if (!esEntero(precioCentavos) || precioCentavos <= 0)
    throw new ErrorDeDominio('PRECIO_INVALIDO', 'El precio no es válido.');
  if (precioCentavos < variante.precioMinimo)
    throw new ErrorDeDominio('PRECIO_BAJO_MINIMO', `El precio está por debajo del mínimo (${variante.sku}).`);
  if (precioCentavos > variante.precioMaximo)
    throw new ErrorDeDominio('PRECIO_SOBRE_MAXIMO', `El precio supera el máximo (${variante.sku}).`);
}
