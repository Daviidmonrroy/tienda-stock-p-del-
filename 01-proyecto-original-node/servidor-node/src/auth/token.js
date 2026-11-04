import { createHmac, timingSafeEqual } from 'node:crypto';

const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');

export function firmar(carga, secreto, duracionSeg = 8 * 3600) {
  const cuerpo = `${b64({ alg: 'HS256', typ: 'JWT' })}.${b64({ ...carga, exp: Math.floor(Date.now() / 1000) + duracionSeg })}`;
  return `${cuerpo}.${createHmac('sha256', secreto).update(cuerpo).digest('base64url')}`;
}
export function leer(token, secreto) {
  const partes = String(token ?? '').split('.');
  if (partes.length !== 3) return null;
  const esperado = createHmac('sha256', secreto).update(`${partes[0]}.${partes[1]}`).digest();
  const real = Buffer.from(partes[2], 'base64url');
  if (esperado.length !== real.length || !timingSafeEqual(esperado, real)) return null;
  const carga = JSON.parse(Buffer.from(partes[1], 'base64url').toString());
  return carga.exp > Date.now() / 1000 ? carga : null;
}
