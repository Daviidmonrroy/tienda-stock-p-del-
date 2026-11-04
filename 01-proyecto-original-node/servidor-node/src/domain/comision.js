// Un único porcentaje para todos los productos, en puntos básicos (1000 = 10 %).
export function comisionCentavos(totalLineaCentavos, bp) {
  return Math.round((totalLineaCentavos * bp) / 10000);
}
