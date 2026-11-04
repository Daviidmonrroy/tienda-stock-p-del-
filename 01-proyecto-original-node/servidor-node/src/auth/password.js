import { scryptSync, randomBytes, timingSafeEqual } from 'node:crypto';

export function hashear(clave) {
  const sal = randomBytes(16);
  const h = scryptSync(clave, sal, 64);
  return `scrypt$${sal.toString('hex')}$${h.toString('hex')}`;
}
export function verificar(clave, guardado) {
  const [alg, sal, h] = guardado.split('$');
  if (alg !== 'scrypt') return false;
  const calc = scryptSync(clave, Buffer.from(sal, 'hex'), 64);
  const real = Buffer.from(h, 'hex');
  return calc.length === real.length && timingSafeEqual(calc, real);
}
