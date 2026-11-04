import { test } from 'node:test';
import assert from 'node:assert/strict';
import { hashear, verificar } from '../src/auth/password.js';
import { firmar, leer } from '../src/auth/token.js';

test('hash de clave: verifica la correcta y rechaza la incorrecta', () => {
  const h = hashear('hola-123');
  assert.ok(verificar('hola-123', h));
  assert.ok(!verificar('hola-124', h));
  assert.notEqual(hashear('hola-123'), h); // sal distinta cada vez
});
test('token: ida y vuelta y manipulación', () => {
  const t = firmar({ sub: 5 }, 'secreto-largo-de-prueba');
  assert.equal(leer(t, 'secreto-largo-de-prueba').sub, 5);
  const [a, , c] = t.split('.');
  const falso = `${a}.${Buffer.from(JSON.stringify({ sub: 1, exp: 9999999999 })).toString('base64url')}.${c}`;
  assert.equal(leer(falso, 'secreto-largo-de-prueba'), null);
});
