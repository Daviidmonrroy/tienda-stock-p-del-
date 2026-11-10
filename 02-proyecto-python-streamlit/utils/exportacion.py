"""Exportación a CSV (separador ';' y coma decimal para que Excel en español lo abra bien)."""
import csv
import io
from decimal import Decimal


def a_csv(filas: list[dict]) -> str:
    if not filas:
        return ""
    salida = io.StringIO()
    escritor = csv.DictWriter(salida, fieldnames=list(filas[0]), delimiter=";", lineterminator="\n")
    escritor.writeheader()
    for fila in filas:
        escritor.writerow({k: (str(v).replace(".", ",") if isinstance(v, Decimal) else v) for k, v in fila.items()})
    return salida.getvalue()
