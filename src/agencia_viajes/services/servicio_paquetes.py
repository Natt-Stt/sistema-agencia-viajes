"""Reglas de negocio de paquetes (RF08 a RF12)."""
from datetime import date

from ..autorizacion import exigir_administrador
from ..errores import ErrorAgencia, ErrorNegocio, ErrorValidacion
from ..models.administrador import Administrador
from ..models.cliente import Cliente
from ..models.paquete import EstadoPaquete, Paquete


class ServicioPaquetes:
    def __init__(self, repositorio, repositorio_destinos, repositorio_reservas=None,
                 reloj=date.today):
        self._repo = repositorio
        self._destinos = repositorio_destinos
        self._reservas = repositorio_reservas
        self._reloj = reloj

    def crear(self, actor, nombre, fecha_salida, fecha_regreso, cupo_maximo,
              ids_destinos, margen=0.20, temporada=""):
        exigir_administrador(actor)
        destinos = self._resolver_destinos(ids_destinos)
        paquete = Paquete(nombre, fecha_salida, fecha_regreso, cupo_maximo,
                          destinos, margen, temporada)
        return self._repo.guardar(paquete)

    def modificar_borrador(self, actor, id_paquete, **datos):
        exigir_administrador(actor)
        paquete = self._obtener(id_paquete)
        if paquete.estado is not EstadoPaquete.BORRADOR:
            raise ErrorNegocio("Solo se pueden modificar paquetes en borrador.")
        permitidos = {"nombre", "fecha_salida", "fecha_regreso", "cupo_maximo",
                      "ids_destinos", "margen", "temporada"}
        if set(datos) - permitidos:
            raise ErrorValidacion("Hay campos no modificables en el paquete.")
        valores = {
            "nombre": paquete.nombre, "fecha_salida": paquete.fecha_salida,
            "fecha_regreso": paquete.fecha_regreso, "cupo_maximo": paquete.cupo_maximo,
            "margen": paquete.margen, "temporada": paquete.temporada,
        }
        valores.update({clave: valor for clave, valor in datos.items() if clave != "ids_destinos"})
        destinos = (self._resolver_destinos(datos["ids_destinos"])
                    if "ids_destinos" in datos else paquete.destinos)
        actualizado = Paquete(**valores, destinos=destinos, id_paquete=paquete.id)
        return self._repo.guardar(actualizado)

    def publicar(self, actor, id_paquete):
        exigir_administrador(actor)
        paquete = self._obtener(id_paquete)
        if paquete.estado is not EstadoPaquete.BORRADOR:
            raise ErrorNegocio("El paquete ya fue publicado.")
        paquete.destinos = self._resolver_destinos([destino.id for destino in paquete.destinos])
        paquete.precio_por_persona = paquete.calcular_precio()
        paquete.publicar()
        return self._repo.guardar(paquete)

    def listar(self, actor):
        exigir_administrador(actor)
        return [(paquete, self._cupo_disponible(paquete)) for paquete in self._repo.listar()]

    def listar_publicados(self, actor):
        if not isinstance(actor, (Administrador, Cliente)):
            raise ErrorAgencia("Debes iniciar sesión para consultar paquetes.")
        hoy = self._reloj().isoformat()
        resultados = []
        for paquete in self._repo.listar(solo_publicados=True):
            disponible = self._cupo_disponible(paquete)
            if paquete.fecha_salida >= hoy and disponible > 0:
                resultados.append((paquete, disponible))
        return resultados

    def _resolver_destinos(self, ids_destinos):
        if not isinstance(ids_destinos, (list, tuple)) or not 2 <= len(ids_destinos) <= 5:
            raise ErrorValidacion("Un paquete debe incluir entre 2 y 5 destinos.")
        if any(isinstance(item, bool) or not isinstance(item, int) or item <= 0
               for item in ids_destinos):
            raise ErrorValidacion("Los identificadores de destino no son válidos.")
        if len(set(ids_destinos)) != len(ids_destinos):
            raise ErrorValidacion("No se puede repetir un destino en el paquete.")
        destinos = self._destinos.disponibles_por_ids(ids_destinos)
        if len(destinos) != len(ids_destinos):
            raise ErrorNegocio("Todos los destinos deben existir y estar disponibles.")
        return destinos

    def _cupo_disponible(self, paquete):
        ocupados = self._reservas.reservas_activas(paquete.id) if self._reservas else 0
        return max(0, paquete.cupo_maximo - ocupados)

    def _obtener(self, id_paquete):
        paquete = self._repo.buscar(id_paquete)
        if paquete is None:
            raise ErrorNegocio("El paquete indicado no existe.")
        return paquete