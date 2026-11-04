// Almacén en memoria: sirve para pruebas y demo. El adaptador MySQL implementa la misma interfaz.
import { randomUUID } from 'node:crypto';
import { hashear } from '../auth/password.js';

export function crearAlmacen({ comisionBp = 1000 } = {}) {
  const usuarios = new Map();
  const ubicaciones = new Map();
  const variantes = new Map();
  const stock = new Map(); // `${varianteId}:${ubicacionId}` -> cantidad
  const ventas = [];
  const movimientos = [];
  let seq = 1;
  const k = (v, u) => `${v}:${u}`;

  return {
    comisionBp,
    ventas, movimientos,
    agregarUbicacion: (u) => (ubicaciones.set(u.id, u), u),
    agregarUsuario: ({ clave, ...u }) => {
      const usr = { activo: true, ...u, passwordHash: hashear(clave) };
      usuarios.set(usr.id, usr); return usr;
    },
    agregarVariante: (v) => (variantes.set(v.id, v), v),
    usuarioPorEmail: (email) => [...usuarios.values()].find((u) => u.email === email && u.activo),
    usuario: (id) => usuarios.get(id),
    ubicacion: (id) => ubicaciones.get(id),
    variantes: () => variantes,
    stockDe: (varianteId, ubicacionId) => stock.get(k(varianteId, ubicacionId)) ?? 0,
    ingresarStock(varianteId, ubicacionId, cantidad, usuarioId, tipo = 'ajuste') {
      stock.set(k(varianteId, ubicacionId), (stock.get(k(varianteId, ubicacionId)) ?? 0) + cantidad);
      movimientos.push({ id: seq++, varianteId, ubicacionId, tipo, cantidad, usuarioId });
    },
    // Equivale a una transacción: guarda venta, movimientos y saldo juntos.
    registrarVenta({ uuidCliente, ubicacionId, vendedorId, clienteId, medioPago, prepara, usuarioId }) {
      const previa = ventas.find((v) => v.uuidCliente === uuidCliente);
      if (previa) return { venta: previa, repetida: true };
      const venta = {
        id: seq++, uuidCliente: uuidCliente ?? randomUUID(), ubicacionId, vendedorId, clienteId,
        medioPago, total: prepara.total, pagado: prepara.pagado, estado: 'confirmada',
        fecha: new Date().toISOString(), items: prepara.lineas,
      };
      ventas.push(venta);
      for (const l of prepara.lineas) {
        stock.set(k(l.varianteId, ubicacionId), this.stockDe(l.varianteId, ubicacionId) - l.cantidad);
        movimientos.push({ id: seq++, varianteId: l.varianteId, ubicacionId, tipo: 'venta', cantidad: -l.cantidad, usuarioId, ref: venta.id });
      }
      return { venta, repetida: false };
    },
  };
}
