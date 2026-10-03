"""Reglas de negocio de los destinos (RF03 a RF07).

Desde el Sprint 2 cada operación recibe el `actor` (quién la pide) y exige que sea
Administrador (RNF04, RN08, S6). Esa comprobación vive aquí, en el servicio.

El servicio coordina: valida con el modelo, decide qué hacer según las reglas
(por ejemplo R8) y delega el guardado al repositorio.
"""
from ..autorizacion import exigir_administrador
from ..errores import ErrorNegocio
from ..models.destino import Destino
from ..repositories.repositorio_destinos import RepositorioDestinos

ELIMINADO = "ELIMINADO"
DESACTIVADO = "DESACTIVADO"


class ServicioDestinos:
    def __init__(self, repositorio: RepositorioDestinos):
        self._repo = repositorio

    def registrar(self, actor, nombre, zona, duracion_dias, costo_base, descripcion="") -> Destino:
        """RF03. Las validaciones R1 y R2 ocurren al construir el Destino."""
        exigir_administrador(actor)
        destino = Destino(nombre, zona, duracion_dias, costo_base, descripcion)
        return self._repo.guardar(destino)

    def modificar(self, actor, id_destino, nombre=None, zona=None, duracion_dias=None,
                  costo_base=None, descripcion=None) -> Destino:
        """RF04. Solo cambia los campos recibidos (los None se dejan igual).

        R7: cambiar el costo de un destino NO altera paquetes ya publicados,
        porque cada paquete guarda su propio precio_por_persona.
        """
        exigir_administrador(actor)
        destino = self._obtener(id_destino)
        if nombre is not None:
            destino.nombre = nombre
        if zona is not None:
            destino.zona = zona
        if duracion_dias is not None:
            destino.duracion_dias = duracion_dias
        if costo_base is not None:
            destino.costo_base = costo_base
        if descripcion is not None:
            destino.descripcion = descripcion
        return self._repo.guardar(destino)

    def listar(self, actor, solo_disponibles: bool = False) -> list[Destino]:
        """RF05."""
        exigir_administrador(actor)
        return self._repo.listar(solo_disponibles)

    def retirar(self, actor, id_destino) -> str:
        """RF06 y RF07, regla R8.

        - Si el destino NO está en ningún paquete: se elimina.
        - Si está en alguno: se marca no disponible (los paquetes ya vendidos
          conservan su contenido y el destino deja de ofrecerse para nuevos).
        """
        exigir_administrador(actor)
        destino = self._obtener(id_destino)
        if self._repo.esta_en_paquete(destino.id):
            destino.marcar_no_disponible()
            self._repo.guardar(destino)
            return DESACTIVADO
        self._repo.eliminar(destino.id)
        return ELIMINADO

    def _obtener(self, id_destino) -> Destino:
        destino = self._repo.buscar(id_destino)
        if destino is None:
            raise ErrorNegocio("El destino indicado no existe.")
        return destino
