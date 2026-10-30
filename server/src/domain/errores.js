export class ErrorDeDominio extends Error {
  constructor(codigo, mensaje, estado = 400) {
    super(mensaje);
    this.codigo = codigo;
    this.estado = estado;
  }
}
