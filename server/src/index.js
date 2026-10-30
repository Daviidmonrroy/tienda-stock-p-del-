// Arranque en modo demo (datos en memoria). El adaptador MySQL se conecta en la etapa siguiente.
import { crearApp } from './http/app.js';
import { crearAlmacen } from './store/memoria.js';

const secreto = process.env.JWT_SECRET;
if (!secreto) { console.error('Definí JWT_SECRET (ver .env.example).'); process.exit(1); }

const almacen = crearAlmacen({ comisionBp: Number(process.env.COMISION_BP ?? 1000) });
almacen.agregarUbicacion({ id: 1, nombre: 'Local', tipo: 'local' });
almacen.agregarUbicacion({ id: 2, nombre: 'Cancha', tipo: 'cancha' });
almacen.agregarUsuario({ id: 1, nombre: 'Dueño', email: 'admin@demo.local', clave: process.env.DEMO_CLAVE ?? 'cambiar-esta-clave', rol: 'admin' });

crearApp({ almacen, secreto }).listen(Number(process.env.PORT ?? 3000), () =>
  console.log(`API en http://localhost:${process.env.PORT ?? 3000}`));
