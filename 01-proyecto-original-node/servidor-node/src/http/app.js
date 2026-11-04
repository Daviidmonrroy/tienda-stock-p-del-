import { createServer } from 'node:http';
import { verificar } from '../auth/password.js';
import { firmar, leer } from '../auth/token.js';
import { ErrorDeDominio } from '../domain/errores.js';
import { prepararVenta } from '../domain/ventas.js';

const json = (res, estado, cuerpo) => {
  res.writeHead(estado, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(cuerpo));
};
const leerCuerpo = (req) => new Promise((ok, mal) => {
  let d = '';
  req.on('data', (c) => { d += c; if (d.length > 1e6) { mal(new ErrorDeDominio('CUERPO_GRANDE', 'Pedido demasiado grande.', 413)); req.destroy(); } });
  req.on('end', () => { try { ok(d ? JSON.parse(d) : {}); } catch { mal(new ErrorDeDominio('JSON_INVALIDO', 'JSON inválido.')); } });
});

// El vendedor nunca recibe el costo; ve precio mínimo y máximo.
const vistaVariante = (v, rol) => {
  const { costo, ...publico } = v;
  return rol === 'admin' ? v : publico;
};

export function crearApp({ almacen, secreto }) {
  if (!secreto || secreto.length < 16) throw new Error('Falta JWT_SECRET (mínimo 16 caracteres).');

  async function manejar(req, res) {
    const url = new URL(req.url, 'http://x');
    const ruta = `${req.method} ${url.pathname}`;

    if (ruta === 'GET /api/salud') return json(res, 200, { ok: true });

    if (ruta === 'POST /api/login') {
      const { email, clave } = await leerCuerpo(req);
      const u = almacen.usuarioPorEmail(email);
      if (!u || !verificar(String(clave ?? ''), u.passwordHash))
        throw new ErrorDeDominio('CREDENCIALES', 'Email o clave incorrectos.', 401);
      const token = firmar({ sub: u.id, rol: u.rol }, secreto);
      return json(res, 200, { token, usuario: { id: u.id, nombre: u.nombre, rol: u.rol } });
    }

    const carga = leer((req.headers.authorization ?? '').replace(/^Bearer /, ''), secreto);
    if (!carga) throw new ErrorDeDominio('NO_AUTORIZADO', 'Iniciá sesión.', 401);
    const yo = almacen.usuario(carga.sub);
    if (!yo || !yo.activo) throw new ErrorDeDominio('NO_AUTORIZADO', 'Usuario inactivo.', 401);

    if (ruta === 'GET /api/productos')
      return json(res, 200, [...almacen.variantes().values()].map((v) => vistaVariante(v, yo.rol)));

    if (ruta === 'GET /api/stock') {
      const ubi = yo.rol === 'admin' ? Number(url.searchParams.get('ubicacion')) : yo.ubicacionId;
      const filas = [...almacen.variantes().keys()].map((id) => ({ varianteId: id, cantidad: almacen.stockDe(id, ubi) }));
      return json(res, 200, { ubicacionId: ubi, stock: filas });
    }

    if (ruta === 'POST /api/ventas') {
      const cuerpo = await leerCuerpo(req);
      // Empleados y vendedores solo venden desde su propio lugar; el admin elige.
      const ubicacionId = yo.rol === 'admin' ? cuerpo.ubicacionId : yo.ubicacionId;
      if (!almacen.ubicacion(ubicacionId)) throw new ErrorDeDominio('UBICACION_INVALIDA', 'Ubicación inválida.');
      const vendedorId = yo.rol === 'vendedor' ? yo.id : null;
      const prepara = prepararVenta(cuerpo, {
        variantes: almacen.variantes(),
        stockDe: (id) => almacen.stockDe(id, ubicacionId),
        comisionBp: almacen.comisionBp,
        vendedorId,
      });
      const { venta, repetida } = almacen.registrarVenta({
        uuidCliente: cuerpo.uuid, ubicacionId, vendedorId, clienteId: cuerpo.clienteId ?? null,
        medioPago: cuerpo.medioPago, prepara, usuarioId: yo.id,
      });
      return json(res, repetida ? 200 : 201, venta);
    }

    throw new ErrorDeDominio('NO_ENCONTRADO', 'Ruta inexistente.', 404);
  }

  return createServer((req, res) => {
    manejar(req, res).catch((e) => {
      if (e instanceof ErrorDeDominio) return json(res, e.estado, { error: e.codigo, mensaje: e.message });
      console.error(e);
      json(res, 500, { error: 'ERROR_INTERNO', mensaje: 'Algo salió mal.' });
    });
  });
}
