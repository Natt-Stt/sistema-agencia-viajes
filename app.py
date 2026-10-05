"""Interfaz web de Viajes Aventura. Ejecutar con: streamlit run app.py"""
from datetime import date, timedelta

import streamlit as st

from src.agencia_viajes.database import crear_esquema, obtener_conexion
from src.agencia_viajes.errores import ErrorAgencia
from src.agencia_viajes.models.administrador import Administrador
from src.agencia_viajes.repositories.repositorio_destinos import RepositorioDestinos
from src.agencia_viajes.repositories.repositorio_paquetes import RepositorioPaquetes
from src.agencia_viajes.repositories.repositorio_reservas import RepositorioReservas
from src.agencia_viajes.repositories.repositorio_usuarios import RepositorioUsuarios
from src.agencia_viajes.seguridad import cargar_cifrador
from src.agencia_viajes.services.servicio_autenticacion import ServicioAutenticacion
from src.agencia_viajes.services.servicio_destinos import DESACTIVADO, ELIMINADO, ServicioDestinos
from src.agencia_viajes.services.servicio_paquetes import ServicioPaquetes
from src.agencia_viajes.services.servicio_reservas import ServicioReservas


st.set_page_config(page_title="Viajes Aventura", page_icon="✦", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --ink: #18322d;
        --muted: #60756e;
        --green: #176b59;
        --green-dark: #104b40;
        --mint: #e7f2ed;
        --coral: #c4674d;
        --paper: #f4f7f3;
        --line: #d8e2dc;
    }
    .stApp {
        background: linear-gradient(130deg, #f5f8f4 0%, #edf3ef 48%, #f8f7f1 100%);
        color: var(--ink);
    }
    [data-testid="stSidebar"] {
        background: #183c35;
        border-right: 1px solid #31574e;
    }
    [data-testid="stSidebar"] * { color: #edf5f0; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { color: #edf5f0; }
    h1, h2, h3 { color: var(--ink); font-family: Georgia, "Times New Roman", serif; }
    h1 { font-size: 2.55rem; font-weight: 500; }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid var(--line);
        border-left: 3px solid var(--green);
        border-radius: 4px;
        padding: 14px 16px;
    }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid var(--line);
        border-radius: 5px;
        padding: 1.2rem;
    }
    div.stButton > button[kind="primary"], div.stFormSubmitButton > button {
        background: var(--green);
        border-color: var(--green);
        color: white;
        border-radius: 4px;
        min-height: 2.7rem;
    }
    div.stButton > button[kind="primary"]:hover,
    div.stFormSubmitButton > button:hover { background: var(--green-dark); border-color: var(--green-dark); }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 4px; }
    [data-testid="stTabs"] button[aria-selected="true"] { color: var(--green); }
    [data-testid="stTabs"] button { color: var(--muted) !important; }
    [data-testid="stTabs"] button[aria-selected="true"] { color: var(--green) !important; }
    [data-testid="stTabs"] button[aria-selected="true"] p { color: var(--green) !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _contexto():
    if "_contexto_viajes" not in st.session_state:
        conexion = obtener_conexion(check_same_thread=False)
        crear_esquema(conexion)
        cifrador = cargar_cifrador()
        repo_usuarios = RepositorioUsuarios(conexion, cifrador)
        repo_destinos = RepositorioDestinos(conexion)
        repo_paquetes = RepositorioPaquetes(conexion)
        repo_reservas = RepositorioReservas(conexion)
        st.session_state["_contexto_viajes"] = {
            "conexion": conexion,
            "auth": ServicioAutenticacion(repo_usuarios),
            "destinos": ServicioDestinos(repo_destinos),
            "paquetes": ServicioPaquetes(repo_paquetes, repo_destinos, repo_reservas),
            "reservas": ServicioReservas(repo_reservas, repo_paquetes),
        }
    return st.session_state["_contexto_viajes"]


def _pesos(valor):
    return "$" + f"{valor:,}".replace(",", ".")


def _error(accion):
    try:
        accion()
    except ErrorAgencia as error:
        st.error(str(error))
        return False
    return True


def _tabla_paquetes(paquetes):
    if not paquetes:
        st.info("No hay paquetes disponibles.")
        return
    filas = []
    for paquete, cupo in paquetes:
        filas.append({
            "Paquete": paquete.nombre,
            "Destinos": " · ".join(destino.nombre for destino in paquete.destinos),
            "Salida": paquete.fecha_salida,
            "Regreso": paquete.fecha_regreso,
            "Precio por persona": _pesos(paquete.precio_por_persona),
            "Cupo disponible": f"{cupo} de {paquete.cupo_maximo}",
            "Estado": paquete.estado.value,
        })
    st.dataframe(filas, hide_index=True, use_container_width=True)


def _tabla_reservas(reservas):
    if not reservas:
        st.info("No hay reservas para mostrar.")
        return
    st.dataframe(
        [{
            "Reserva": reserva.id,
            "Paquete": reserva.nombre_paquete or f"Paquete {reserva.id_paquete}",
            "Personas": reserva.cantidad_personas,
            "Total": _pesos(reserva.total),
            "Fecha": reserva.fecha_emision,
            "Estado": reserva.estado.value,
        } for reserva in reservas],
        hide_index=True,
        use_container_width=True,
    )


def _iniciar_sesion(servicios):
    st.title("Viajes Aventura")
    st.caption("Reservas y escapadas, en un solo lugar.")
    tab_login, tab_registro = st.tabs(["Iniciar sesión", "Crear cuenta"])

    with tab_login:
        with st.form("form_login"):
            correo = st.text_input("Correo electrónico", autocomplete="email")
            password = st.text_input("Contraseña", type="password", autocomplete="current-password")
            enviar = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if enviar:
            try:
                st.session_state["usuario_viajes"] = servicios["auth"].iniciar_sesion(correo, password)
                st.rerun()
            except ErrorAgencia as error:
                st.error(str(error))

    with tab_registro:
        with st.form("form_registro", clear_on_submit=False):
            nombre = st.text_input("Nombre completo")
            rut = st.text_input(
                "RUT",
                placeholder="12.345.678-5",
                help="Puedes escribirlo con o sin puntos y guion. El dígito verificador debe ser correcto.",
            )
            correo_nuevo = st.text_input("Correo electrónico", key="registro_correo", autocomplete="email")
            telefono = st.text_input("Teléfono", placeholder="+56 9 1234 5678")
            clave = st.text_input("Contraseña", type="password", autocomplete="new-password")
            repetir = st.text_input("Repetir contraseña", type="password", autocomplete="new-password")
            registrar = st.form_submit_button("Crear cuenta", type="primary", use_container_width=True)
        if registrar:
            if clave != repetir:
                st.error("Las contraseñas no coinciden.")
            elif _error(lambda: servicios["auth"].registrar_cliente(
                nombre, rut, correo_nuevo, telefono, clave
            )):
                st.success("Cuenta creada. Ya puedes iniciar sesión.")


def _sidebar(usuario):
    with st.sidebar:
        st.markdown("### VIAJES\n# Aventura")
        st.caption(usuario.nombre)
        st.caption("Administración" if isinstance(usuario, Administrador) else "Área de cliente")
        paginas = (["Resumen", "Destinos", "Paquetes", "Reservas"]
                   if isinstance(usuario, Administrador)
                   else ["Explorar paquetes", "Mis reservas", "Mi perfil"])
        pagina = st.radio("Navegación", paginas, label_visibility="collapsed")
        st.divider()
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.pop("usuario_viajes", None)
            st.rerun()
    return pagina


def _pagina_resumen(servicios, usuario):
    st.title("Resumen")
    paquetes = servicios["paquetes"].listar(usuario)
    destinos = servicios["destinos"].listar(usuario)
    reservas = servicios["reservas"].listar_para_administrador(usuario)
    pendientes = sum(reserva.estado.value == "PENDIENTE" for reserva in reservas)
    columnas = st.columns(4)
    columnas[0].metric("Paquetes", len(paquetes))
    columnas[1].metric("Publicados", sum(p.estado.value == "PUBLICADO" for p, _ in paquetes))
    columnas[2].metric("Destinos activos", sum(d.disponible for d in destinos))
    columnas[3].metric("Reservas pendientes", pendientes)
    st.subheader("Paquetes recientes")
    _tabla_paquetes(paquetes[:6])


def _pagina_destinos(servicios, usuario):
    mensaje_destino_creado = st.session_state.pop("mensaje_destino_creado", None)
    if mensaje_destino_creado:
        st.success(mensaje_destino_creado)

    st.title("Destinos")
    st.dataframe([{
        "ID": destino.id,
        "Nombre": destino.nombre,
        "Zona": destino.zona,
        "Duración": f"{destino.duracion_dias} días",
        "Costo base": _pesos(destino.costo_base),
        "Disponibilidad": "Disponible" if destino.disponible else "No disponible",
    } for destino in servicios["destinos"].listar(usuario)], hide_index=True, use_container_width=True)

    alta, cambios = st.tabs(["Registrar destino", "Modificar o retirar"])
    with alta:
        with st.form("crear_destino", clear_on_submit=True):
            columnas = st.columns(2)
            nombre = columnas[0].text_input("Nombre")
            zona = columnas[1].text_input("Zona")
            descripcion = st.text_area("Descripción")
            columnas = st.columns(2)
            duracion = columnas[0].number_input("Duración en días", min_value=1, step=1)
            costo = columnas[1].number_input("Costo base (CLP)", min_value=1, step=1000)
            guardar = st.form_submit_button("Registrar destino", type="primary")
        if guardar and _error(lambda: servicios["destinos"].registrar(
            usuario, nombre, zona, int(duracion), int(costo), descripcion
        )):
            st.session_state["mensaje_destino_creado"] = "Destino registrado correctamente."
            st.rerun()

    with cambios:
        destinos = servicios["destinos"].listar(usuario)
        if not destinos:
            st.info("No hay destinos registrados.")
            return
        elegido = st.selectbox("Destino", destinos, format_func=lambda d: f"{d.id} · {d.nombre}")
        with st.form("editar_destino"):
            columnas = st.columns(2)
            nombre_nuevo = columnas[0].text_input("Nombre", value=elegido.nombre)
            zona_nueva = columnas[1].text_input("Zona", value=elegido.zona)
            descripcion_nueva = st.text_area("Descripción", value=elegido.descripcion)
            columnas = st.columns(2)
            duracion_nueva = columnas[0].number_input(
                "Duración en días", min_value=1, value=elegido.duracion_dias, step=1
            )
            costo_nuevo = columnas[1].number_input(
                "Costo base (CLP)", min_value=1, value=elegido.costo_base, step=1000
            )
            columnas = st.columns(2)
            actualizar = columnas[0].form_submit_button("Guardar cambios", type="primary")
            retirar = columnas[1].form_submit_button("Retirar destino")
        if actualizar and _error(lambda: servicios["destinos"].modificar(
            usuario, elegido.id, nombre_nuevo, zona_nueva, int(duracion_nueva),
            int(costo_nuevo), descripcion_nueva
        )):
            st.success("Destino actualizado.")
            st.rerun()
        if retirar:
            resultado = []
            if _error(lambda: resultado.append(servicios["destinos"].retirar(usuario, elegido.id))):
                st.success("Destino eliminado." if resultado[0] == ELIMINADO
                           else "Destino marcado como no disponible.")
                st.rerun()


def _pagina_paquetes_admin(servicios, usuario):
    st.title("Paquetes")
    paquetes = servicios["paquetes"].listar(usuario)
    _tabla_paquetes(paquetes)
    crear, editar = st.tabs(["Crear borrador", "Editar o publicar"])
    destinos = servicios["destinos"].listar(usuario, solo_disponibles=True)

    with crear:
        if len(destinos) < 2:
            st.info("Registra al menos dos destinos disponibles para crear un paquete.")
        else:
            with st.form("crear_paquete"):
                nombre = st.text_input("Nombre del paquete")
                temporada = st.text_input("Temporada")
                columnas = st.columns(2)
                salida = columnas[0].date_input("Fecha de salida", value=date.today() + timedelta(days=30))
                regreso = columnas[1].date_input("Fecha de regreso", value=date.today() + timedelta(days=33))
                columnas = st.columns(2)
                cupo = columnas[0].number_input("Cupo máximo", min_value=1, value=12, step=1)
                margen = columnas[1].number_input("Margen (%)", min_value=0.0, value=20.0, step=1.0)
                seleccionados = st.multiselect(
                    "Destinos (2 a 5)", destinos, format_func=lambda d: f"{d.id} · {d.nombre}"
                )
                crear = st.form_submit_button("Guardar como borrador", type="primary")
            if crear and _error(lambda: servicios["paquetes"].crear(
                usuario, nombre, salida.isoformat(), regreso.isoformat(), int(cupo),
                [destino.id for destino in seleccionados], margen / 100, temporada
            )):
                st.success("Borrador creado.")
                st.rerun()

    with editar:
        borradores = [paquete for paquete, _ in paquetes if paquete.estado.value == "BORRADOR"]
        if not borradores:
            st.info("No hay paquetes en borrador.")
        else:
            elegido = st.selectbox("Borrador", borradores, format_func=lambda p: f"{p.id} · {p.nombre}")
            destinos_por_id = {destino.id: destino for destino in destinos}
            with st.form("editar_paquete"):
                nombre_nuevo = st.text_input("Nombre", value=elegido.nombre)
                columnas = st.columns(2)
                salida_nueva = columnas[0].date_input(
                    "Fecha de salida", value=date.fromisoformat(elegido.fecha_salida), key="salida_edicion"
                )
                regreso_nuevo = columnas[1].date_input(
                    "Fecha de regreso", value=date.fromisoformat(elegido.fecha_regreso), key="regreso_edicion"
                )
                columnas = st.columns(2)
                cupo_nuevo = columnas[0].number_input(
                    "Cupo máximo", min_value=1, value=elegido.cupo_maximo, step=1, key="cupo_edicion"
                )
                margen_nuevo = columnas[1].number_input(
                    "Margen (%)", min_value=0.0, value=elegido.margen * 100, step=1.0, key="margen_edicion"
                )
                temporada_nueva = st.text_input("Temporada", value=elegido.temporada)
                destinos_nuevos = st.multiselect(
                    "Destinos", list(destinos_por_id),
                    default=[d.id for d in elegido.destinos if d.id in destinos_por_id],
                    format_func=lambda id_destino: f"{id_destino} · {destinos_por_id[id_destino].nombre}",
                    key="destinos_edicion"
                )
                columnas = st.columns(2)
                guardar = columnas[0].form_submit_button("Guardar borrador", type="primary")
                publicar = columnas[1].form_submit_button("Publicar y fijar precio")
            if guardar and _error(lambda: servicios["paquetes"].modificar_borrador(
                usuario, elegido.id, nombre=nombre_nuevo, fecha_salida=salida_nueva.isoformat(),
                fecha_regreso=regreso_nuevo.isoformat(), cupo_maximo=int(cupo_nuevo),
                margen=margen_nuevo / 100, temporada=temporada_nueva,
                ids_destinos=destinos_nuevos
            )):
                st.success("Borrador actualizado.")
                st.rerun()
            if publicar:
                resultado = []
                if _error(lambda: resultado.append(
                    servicios["paquetes"].publicar(usuario, elegido.id)
                )):
                    st.success(f"Publicado a {_pesos(resultado[0].precio_por_persona)} por persona.")
                    st.rerun()


def _pagina_reservas_admin(servicios, usuario):
    st.title("Reservas")
    reservas = servicios["reservas"].listar_para_administrador(usuario)
    _tabla_reservas(reservas)
    abiertas = [reserva for reserva in reservas if reserva.estado.value != "CANCELADA"]
    pendientes = [reserva for reserva in abiertas if reserva.estado.value == "PENDIENTE"]
    if not abiertas:
        return
    acciones = st.columns(2)
    with acciones[0]:
        if pendientes:
            seleccion = st.selectbox("Reserva pendiente", pendientes,
                                     format_func=lambda r: f"#{r.id} · {r.nombre_paquete}")
            if st.button("Confirmar reserva", type="primary"):
                if _error(lambda: servicios["reservas"].confirmar(usuario, seleccion.id)):
                    st.success("Reserva confirmada.")
                    st.rerun()
    with acciones[1]:
        seleccion_cancelar = st.selectbox("Reserva activa", abiertas,
                                          format_func=lambda r: f"#{r.id} · {r.nombre_paquete}")
        if st.button("Cancelar reserva"):
            if _error(lambda: servicios["reservas"].cancelar(usuario, seleccion_cancelar.id)):
                st.success("Reserva cancelada.")
                st.rerun()


def _pagina_paquetes_cliente(servicios, usuario):
    st.title("Explorar paquetes")
    paquetes = servicios["paquetes"].listar_publicados(usuario)
    _tabla_paquetes(paquetes)
    if not paquetes:
        return
    opciones = [paquete for paquete, _ in paquetes]
    with st.form("reservar_paquete"):
        elegido = st.selectbox("Paquete", opciones,
                               format_func=lambda p: f"{p.nombre} · {_pesos(p.precio_por_persona)} por persona")
        cupo = next(cupo for paquete, cupo in paquetes if paquete.id == elegido.id)
        personas = st.number_input("Personas", min_value=1, max_value=cupo, value=1, step=1)
        st.caption(f"Total: {_pesos(elegido.precio_por_persona * int(personas))}")
        reservar = st.form_submit_button("Solicitar reserva", type="primary")
    if reservar and _error(lambda: servicios["reservas"].reservar(usuario, elegido.id, int(personas))):
        st.success("Reserva registrada y pendiente de confirmación.")
        st.rerun()


def _pagina_historial(servicios, usuario):
    st.title("Mis reservas")
    reservas = servicios["reservas"].historial(usuario)
    _tabla_reservas(reservas)
    activas = [reserva for reserva in reservas if reserva.estado.value != "CANCELADA"]
    if activas:
        seleccion = st.selectbox("Reserva a cancelar", activas,
                                 format_func=lambda r: f"#{r.id} · {r.nombre_paquete} · {r.estado.value}")
        if st.button("Cancelar reserva"):
            if _error(lambda: servicios["reservas"].cancelar(usuario, seleccion.id)):
                st.success("Reserva cancelada.")
                st.rerun()


def _pagina_perfil(usuario):
    st.title("Mi perfil")
    columnas = st.columns(3)
    columnas[0].metric("Nombre", usuario.nombre)
    columnas[1].metric("RUT", usuario.rut_enmascarado())
    columnas[2].metric("Teléfono", usuario.telefono_enmascarado())
    st.caption(usuario.correo)


def main():
    servicios = _contexto()
    usuario = st.session_state.get("usuario_viajes")
    if usuario is None:
        _iniciar_sesion(servicios)
        return

    pagina = _sidebar(usuario)
    if isinstance(usuario, Administrador):
        if pagina == "Resumen":
            _pagina_resumen(servicios, usuario)
        elif pagina == "Destinos":
            _pagina_destinos(servicios, usuario)
        elif pagina == "Paquetes":
            _pagina_paquetes_admin(servicios, usuario)
        else:
            _pagina_reservas_admin(servicios, usuario)
    elif pagina == "Explorar paquetes":
        _pagina_paquetes_cliente(servicios, usuario)
    elif pagina == "Mis reservas":
        _pagina_historial(servicios, usuario)
    else:
        _pagina_perfil(usuario)


main()