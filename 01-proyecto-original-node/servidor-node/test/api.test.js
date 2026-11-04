import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { crearApp } from '../src/http/app.js';
import { crearAlmacen } from '../src/store/memoria.js';
import { firmar } from '../src/auth/token.js';

let srv, base, almacen;
const SECRETO = 'secreto-de-prueba-123456';

before(async () => {
  almacen = crearAlmacen({ comisionBp: 1000 });
  almacen.agregarUbicacion({ id: 1, nombre: 'Local', tipo: 'local' });
  almacen.agregarUbicacion({ id: 2, nombre: 'Cancha', tipo: 'cancha' });
  almacen.agregarUbicacion({ id: 3, nombre: 'Mochila Ana', tipo: 'vendedor' });
  almacen.agregarUsuario({ id: 1, nombre: 'Dueño', email: 'a@x.com', clave: 'clave-admin', rol: 'admin' });
  almacen.agregarUsuario({ id: 2, nombre: 'Ana', email: 'v@x.com', clave: 'clave-vend', rol: 'vendedor', ubicacionId: 3 });
  almacen.agregarUsuario({ id: 3, nombre: 'Lu', email: 'e@x.com', clave: 'clave-emp', rol: 'empleado', ubicacionId: 2 });
  almacen.agregarVariante({ id: 1, sku: 'PAL-1', costo: 6000000, precioMinimo: 9000000, precioMaximo: 12000000 });
  almacen.ingresarStock(1, 1, 10, 1);
  almacen.ingresarStock(1, 3, 2, 1);
  almacen.ingresarStock(1, 2, 4, 1);
  srv = crearApp({ almacen, secreto: SECRETO });
  await new Promise((r) => srv.listen(0, r));
  base = `http://localhost:${srv.address().port}`;
});
after(() => srv.close());

const pedir = async (ruta, { token, cuerpo, metodo } = {}) => {
  const r = await fetch(base + ruta, {
    method: metodo ?? (cuerpo ? 'POST' : 'GET'),
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  return { estado: r.status, datos: await r.json() };
};
const entrar = async (email, clave) => (await pedir('/api/login', { cuerpo: { email, clave } })).datos.token;
const item = { varianteId: 1, cantidad: 1, precioUnit: 10000000 };

test('login correcto e incorrecto', async () => {
  assert.ok(await entrar('a@x.com', 'clave-admin'));
  assert.equal((await pedir('/api/login', { cuerpo: { email: 'a@x.com', clave: 'mal' } })).estado, 401);
});
test('sin token no se accede', async () => assert.equal((await pedir('/api/productos')).estado, 401));
test('token falsificado o vencido se rechaza', async () => {
  assert.equal((await pedir('/api/productos', { token: firmar({ sub: 1, rol: 'admin' }, 'otro-secreto-distinto') })).estado, 401);
  assert.equal((await pedir('/api/productos', { token: firmar({ sub: 1, rol: 'admin' }, SECRETO, -10) })).estado, 401);
});
test('el vendedor no ve el costo; el admin sí', async () => {
  const v = (await pedir('/api/productos', { token: await entrar('v@x.com', 'clave-vend') })).datos[0];
  assert.equal(v.costo, undefined);
  assert.equal(v.precioMinimo, 9000000);
  assert.equal((await pedir('/api/productos', { token: await entrar('a@x.com', 'clave-admin') })).datos[0].costo, 6000000);
});
test('el vendedor vende de su mochila y genera comisión', async () => {
  const token = await entrar('v@x.com', 'clave-vend');
  const r = await pedir('/api/ventas', { token, cuerpo: { medioPago: 'efectivo', items: [item], ubicacionId: 1 } });
  assert.equal(r.estado, 201);
  assert.equal(r.datos.ubicacionId, 3); // ignora la ubicación pedida
  assert.equal(r.datos.items[0].comision, 1000000);
  assert.equal(almacen.stockDe(1, 3), 1);
  assert.equal(almacen.stockDe(1, 1), 10);
});
test('el empleado vende de su sector y no genera comisión', async () => {
  const r = await pedir('/api/ventas', { token: await entrar('e@x.com', 'clave-emp'), cuerpo: { medioPago: 'transferencia', items: [item] } });
  assert.equal(r.datos.ubicacionId, 2);
  assert.equal(r.datos.items[0].comision, 0);
});
test('no se puede vender fuera del rango de precios ni sin stock', async () => {
  const token = await entrar('a@x.com', 'clave-admin');
  const bajo = await pedir('/api/ventas', { token, cuerpo: { ubicacionId: 1, medioPago: 'efectivo', items: [{ ...item, precioUnit: 1 }] } });
  assert.equal(bajo.datos.error, 'PRECIO_BAJO_MINIMO');
  const mucho = await pedir('/api/ventas', { token, cuerpo: { ubicacionId: 1, medioPago: 'efectivo', items: [{ ...item, cantidad: 99 }] } });
  assert.equal(mucho.estado, 409);
});
test('reenviar la misma venta (offline) no duplica', async () => {
  const token = await entrar('a@x.com', 'clave-admin');
  const cuerpo = { uuid: 'f7a1c2d4-0000-4000-8000-000000000001', ubicacionId: 1, medioPago: 'efectivo', items: [item] };
  const antes = almacen.stockDe(1, 1);
  assert.equal((await pedir('/api/ventas', { token, cuerpo })).estado, 201);
  assert.equal((await pedir('/api/ventas', { token, cuerpo })).estado, 200);
  assert.equal(almacen.stockDe(1, 1), antes - 1);
});
