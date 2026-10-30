// Todos los montos son enteros en centavos. Nunca decimales flotantes.
export const aCentavos = (pesos) => Math.round(pesos * 100);
export const aPesos = (centavos) => centavos / 100;
export const formatear = (centavos) =>
  new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(centavos / 100);
export const esEntero = (n) => Number.isSafeInteger(n);
