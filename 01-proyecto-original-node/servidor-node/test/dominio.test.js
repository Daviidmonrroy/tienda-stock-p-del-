import { test } from 'node:test';
import assert from 'node:assert/strict';
import { prepararVenta } from '../src/domain/ventas.js';
import { comisionCentavos } from '../src/domain/comision.js';

const v = { id: 1, sku: 'PAL-1', costo: 6000000, precioMinimo: 9000000, precioMaximo: 12000000 };
const ctx = (stock = 5, vendedorId = null) => ({
  variantes: new Map([[1, v]]), stockDe: () => stock, comisionBp: 1000, vendedorId,
});
const venta = (extra = {}) => ({ medioPago: 'efectivo', items: [{ varianteId: 1, cantidad: 1, precioUnit: 10000000 }], ...extra });

test('comisión: 10 % de $100.000 son $10.000', () => assert.equal(comisionCentavos(10000000, 1000), 1000000));
test('venta válida calcula total y comisión del vendedor', () => {
  const r = prepararVenta(venta(), ctx(5, 7));
  assert.equal(r.total, 10000000);
  assert.equal(r.lineas[0].comision, 1000000);
  assert.equal(r.lineas[0].costoSnapshot, 6000000);
});
test('venta de mostrador no genera comisión', () => assert.equal(prepararVenta(venta(), ctx()).lineas[0].comision, 0));
test('rechaza precio bajo el mínimo', () =>
  assert.throws(() => prepararVenta(venta({ items: [{ varianteId: 1, cantidad: 1, precioUnit: 8000000 }] }), ctx()), { codigo: 'PRECIO_BAJO_MINIMO' }));
test('rechaza precio sobre el máximo', () =>
  assert.throws(() => prepararVenta(venta({ items: [{ varianteId: 1, cantidad: 1, precioUnit: 13000000 }] }), ctx()), { codigo: 'PRECIO_SOBRE_MAXIMO' }));
test('rechaza sin stock, sumando líneas repetidas', () =>
  assert.throws(() => prepararVenta(venta({ items: [{ varianteId: 1, cantidad: 3, precioUnit: 10000000 }, { varianteId: 1, cantidad: 3, precioUnit: 10000000 }] }), ctx(5)), { codigo: 'SIN_STOCK' }));
test('rechaza cantidades decimales o negativas', () => {
  for (const cantidad of [0, -1, 1.5])
    assert.throws(() => prepararVenta(venta({ items: [{ varianteId: 1, cantidad, precioUnit: 10000000 }] }), ctx()), { codigo: 'CANTIDAD_INVALIDA' });
});
test('fiado exige cliente y calcula saldo', () => {
  assert.throws(() => prepararVenta(venta({ medioPago: 'fiado' }), ctx()), { codigo: 'FIADO_SIN_CLIENTE' });
  const r = prepararVenta(venta({ medioPago: 'fiado', clienteId: 3, pagado: 4000000 }), ctx());
  assert.equal(r.saldo, 6000000);
});
test('fiado no admite pago mayor al total', () =>
  assert.throws(() => prepararVenta(venta({ medioPago: 'fiado', clienteId: 3, pagado: 99999999 }), ctx()), { codigo: 'PAGO_INVALIDO' }));
