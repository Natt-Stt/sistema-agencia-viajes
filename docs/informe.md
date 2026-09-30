# Informe Técnico — Sistema de Agencia de Viajes "Viajes Aventura"

**Asignatura:** TI3021 Programación Orientada a Objeto Seguro 
**Repositorio:** https://github.com/Natt-Stt/sistema-agencia-viajes.git


## 1. Introducción y contexto

### 1.1 Problemática

| # | Problema detectado | Evidencia del caso |
|---|---|---|
| P1 | Reservas duplicadas | 19 duplicadas al cierre |
| P2 | Cupo excedido (sobreventa) | 6 reservas por sobre el cupo |
| P3 | Ventas sobre paquetes vencidos | 3 reservas con fecha de salida pasada |
| P4 | Precio publicado distinto del cobrado | 4 paquetes, por cambio de costo de un destino |
| P5 | Destinos que ya no se operan siguen visibles | 4 de 18 destinos |
| P6 | Consulta de historial lenta y manual | 31 consultas respondidas revisando el cuaderno |
| P7 | Datos sensibles dispersos y sin protección | RUT y teléfono en planilla enviada por correo |
| P8 | Errores de cálculo manual de precio | Paquete publicado a la décima parte de su costo |

### 1.3 Alcance

**Fuera del alcance:** pasarela de pago, facturación electrónica, app móvil, integraciones externas, envío de correos, informes de gestión, contabilidad.



## 2. Requerimientos (criterio 4.1.1)

### 2.1 Requerimientos funcionales

| ID | Requerimiento | Actor | Prioridad | Origen | Criterio de aceptación |
|---|---|---|---|---|---|
| RF01 | El sistema debe permitir registrar un cliente con nombre, RUT, correo, teléfono y contraseña. | Cliente | Must | R9, R10 | Se crea la cuenta con datos válidos; un correo repetido es rechazado; la contraseña se guarda como hash. |
| RF02 | El sistema debe autenticar a clientes y administradores mediante correo y contraseña. | Cliente / Administrador | Must | R10, R11 | Credenciales correctas dan acceso según rol; incorrectas se rechazan con mensaje genérico. |
| RF03 | El sistema debe permitir registrar un destino (nombre, zona, descripción, duración, costo base). | Administrador | Must | R1, R2 | No se acepta nombre repetido ni costo ≤ 0. |
| RF04 | El sistema debe permitir modificar los datos de un destino. | Administrador | Must | R1, R2 | Los cambios se guardan y siguen cumpliendo R1 y R2. |
| RF05 | El sistema debe listar los destinos del catálogo indicando su disponibilidad. | Administrador | Must | R8 | Se muestran los destinos con su estado (disponible / no disponible). |
| RF06 | El sistema debe permitir marcar un destino como no disponible. | Administrador | Must | R8 | El destino deja de ofrecerse para paquetes nuevos y los paquetes ya vendidos conservan su contenido. |
| RF07 | El sistema debe eliminar un destino solo si no forma parte de ningún paquete. | Administrador | Must | R8 | Un destino sin paquetes se elimina; uno con paquetes no se elimina y se ofrece marcarlo no disponible. |
| RF08 | El sistema debe permitir crear un paquete con nombre, fechas, cupo, margen y de 2 a 5 destinos disponibles distintos. | Administrador | Must | R3, R4, R5, R6 | Se rechazan menos de 2 o más de 5 destinos, destinos repetidos, fecha de regreso ≤ salida, cupo ≤ 0 o margen negativo. Margen por defecto: 20 %. |
| RF09 | El sistema debe calcular el precio por persona como la suma de los costos base de los destinos más el margen. | Sistema | Must | R6 | Precio = suma(costos) × (1 + margen). Ejemplo verificable con datos del caso. |
| RF10 | El sistema debe permitir publicar un paquete, fijando su precio. | Administrador | Must | R7 | Tras publicar, un cambio de costo en un destino **no** altera el precio del paquete. |
| RF11 | El sistema debe permitir modificar un paquete mientras esté en borrador. | Administrador | Should | Supuesto S5 | Un paquete publicado no puede cambiar destinos, margen ni precio. |
| RF12 | El sistema debe mostrar los paquetes publicados con su cupo disponible. | Cliente / Administrador | Must | R14, R15 | Cupo disponible = cupo máximo − personas en reservas activas. No se muestran paquetes con salida vencida como reservables. |
| RF13 | El sistema debe permitir a un cliente autenticado registrar una reserva de un paquete. | Cliente | Must | R11–R16 | Se rechaza si personas < 1, si supera el cupo disponible o si la salida ya pasó. El total = precio × personas y queda fijo. |
| RF14 | El sistema debe permitir a un cliente consultar su historial de reservas. | Cliente | Must | R11, R17 | Solo ve sus reservas; no se muestran RUT ni teléfono. |
| RF15 | El sistema debe permitir cancelar una reserva. | Cliente / Administrador | Should | Supuesto S1 | La reserva pasa a CANCELADA y libera el cupo. |
| RF16 | El sistema debe permitir al administrador confirmar una reserva pendiente y registrar quién la confirmó. | Administrador | Should | Supuesto S2, S3 | La reserva pasa de PENDIENTE a CONFIRMADA y queda asociada al administrador. |
| RF17 | El sistema debe permitir al administrador consultar las reservas sin exponer RUT ni teléfono de los clientes. | Administrador | Should | R17 | El listado no incluye datos sensibles. |

### 2.3 Requerimientos no funcionales

| ID | Categoría | Requerimiento | Prioridad | Origen | Cómo se verifica |
|---|---|---|---|---|---|
| RNF01 | Usabilidad | El sistema ofrece un menú por consola con opciones numeradas y mensajes de error claros. | Should | Guía | Un usuario completa una reserva sin instrucciones externas. |
| RNF02 | Rendimiento | Las consultas y operaciones habituales responden en menos de 2 segundos con hasta 1.000 reservas. | Could | Caso (214 reservas/temporada) | Prueba con datos de carga. |
| RNF03 | Seguridad — credenciales | Las contraseñas se almacenan únicamente como hash con un algoritmo adaptativo (bcrypt o argon2). | Must | R10 | Revisión de la BD: ninguna contraseña legible. |
| RNF04 | Seguridad — autorización | Cada rol accede solo a sus funciones; un cliente ve únicamente sus reservas. | Must | R11 | Prueba: un cliente no accede a funciones de administrador ni a reservas ajenas. |
| RNF05 | Seguridad — datos sensibles | RUT y teléfono no aparecen en listados ni en mensajes de error. | Must | R17 | Revisión de salidas y mensajes de error. |
| RNF06 | Seguridad — entradas | Todo dato ingresado se valida y todas las consultas SQL son parametrizadas. | Must | Guía (alcance) | Pruebas con entradas maliciosas (`' OR 1=1 --`). |
| RNF07 | Integridad de datos | La BD impone restricciones (UNIQUE, CHECK, FOREIGN KEY) y las reservas se registran en una transacción. | Must | R1, R2, R9 | Intentos de insertar datos inválidos son rechazados por la BD. |
| RNF08 | Mantenibilidad | Código en capas (modelos, repositorios, servicios, seguridad), PEP 8 y docstrings. | Should | Guía | Revisión de estructura del repositorio. |
| RNF09 | Compatibilidad | Funciona con Python 3.11+ y SQLite en Windows 10/11; dependencias en `requirements.txt`. | Should | Guía | Instalación limpia en otro equipo. |

### 2.4 Reglas de negocio del caso y su traducción a requerimientos

| Regla | Resumen | Cubierta por |
|---|---|---|
| R1 | Destino con nombre, zona, descripción, duración y costo; nombre único | RF03, RF04, RNF07 |
| R2 | Costo base > 0 | RF03, RF04, RNF07 |
| R3 | Paquete de 2 a 5 destinos, sin repetir | RF08 |
| R4 | Un destino puede estar en varios paquetes | RF08 (relación N:M) |
| R5 | Paquete con nombre, fechas coherentes y cupo > 0 | RF08 |
| R6 | Precio = suma de costos + margen (20 % habitual, nunca negativo) | RF08, RF09 |
| R7 | Precio fijo al publicar | RF10 |
| R8 | Destino se elimina si no está en paquetes; si está, se marca no disponible | RF06, RF07 |
| R9 | Cliente con nombre, RUT, correo, teléfono, contraseña; correo único | RF01, RNF07 |
| R10 | Contraseña nunca en claro | RF01, RF02, RNF03 |
| R11 | Solo cliente autenticado reserva y consulta; ve solo lo suyo | RF13, RF14, RNF04 |
| R12 | Reserva = cliente + paquete + fecha + personas + total | RF13 |
| R13 | Total = precio × personas, no cambia | RF13 |
| R14 | No se acepta reserva sobre el cupo disponible | RF12, RF13 |
| R15 | No se acepta reserva con salida pasada | RF12, RF13 |
| R16 | Personas ≥ 1 | RF13 |
| R17 | RUT y teléfono no se muestran en listados ni errores | RF14, RF17, RNF05 |

### 2.5 Supuestos (vacíos del caso)

| ID | Vacío | Supuesto adoptado | Justificación técnica |
|---|---|---|---|
| S1 | ¿Qué pasa cuando un cliente desiste? | La reserva pasa a CANCELADA y libera el cupo. No se borra. | Conserva el historial (P6) y evita los cupos fantasma (P2). |
| S2 | ¿Qué estados tiene una reserva? | PENDIENTE → CONFIRMADA → CANCELADA. Pendiente y Confirmada ocupan cupo. | Refleja el proceso actual (transferencia verificada a mano) sin pasarela de pago. |
| S3 | ¿Quién confirma el pago? | Solo un administrador, tras verificar la transferencia; queda registrado quién. | La verificación automática está fuera del alcance. |
| S4 | ¿Qué pasa con un paquete cuya temporada terminó? | No se elimina; deja de ser reservable comparando con la fecha actual. | Conserva historial y cumple R15. La vigencia se calcula, no se almacena. |
| S5 | ¿Cuándo se congela el precio? (R6 "calcula" vs R7 "fijado al publicar") | El paquete nace en BORRADOR (editable) y al publicarse el precio queda fijo. | Resuelve la ambigüedad y evita P4. |
| S6 | ¿Quién modifica el catálogo? | Solo usuarios con rol Administrador. | Es el rol descrito en el caso (los tres socios). |
| S7 | ¿Cómo nace el primer administrador? | Un script de inicialización lo crea; no existe auto-registro de administradores. | Evita que cualquier persona se otorgue privilegios. |
| S8 | ¿Se permiten reservas duplicadas? | Un cliente no puede tener dos reservas activas del mismo paquete. | Ataca P1 (19 duplicadas). **Decide si lo adoptas.** |


### 2.6 Verificación: ¿los requerimientos resuelven el problema? 


| Problema | Requerimientos que lo resuelven |
|---|---|
| P1 Reservas duplicadas | S8 (si se adopta), RF13 |
| P2 Cupo excedido | RF12, RF13 (R14), RNF07 |
| P3 Paquetes vencidos | RF12, RF13 (R15) |
| P4 Precio distinto del cobrado | RF10 (R7), RF13 (R13) |
| P5 Destinos no operados visibles | RF06 |
| P6 Historial manual | RF14 |
| P7 Datos sensibles sin protección | RF02, RNF03, RNF05 |
| P8 Error de cálculo manual | RF08, RF09, RNF06 |

---

## 3. Modelado 

### 3.1 Diagrama de casos de uso
   ![Diagrama de casos de uso](../docs/img/DiagramaCasosdeuso.jpg)

### 3.2 Diagramas BPMN

- **BPMN 1: Proceso de reserva.**

![  BPNM Proceso de Reserva](../docs/img/BPMN1.jpg)

- **BPMN 2: Creación y publicación de un paquete.**

![  BPNM Creación y Publicación de un paquete](../docs/img/BPMN2.jpg)


### 3.3 Diagrama de clases 

![Modelo de Dominio](../docs/img/Dominio.jpg)

![Diagrama de Servicios y Repositorios](../docs/img/Dominio2.jpg)



### 3.4 Matriz de trazabilidad (indicador 4.1.2.I.8, vale 10 %)

> **Qué va aquí:** la tabla que conecta todo. Cada RF debe aparecer con su caso de uso, su proceso BPMN, su clase, su archivo de código y su prueba. Si una celda queda vacía, hay una inconsistencia. Complétala **a medida que avanzas**, no al final.

| RF | Regla origen | Caso de uso | BPMN | Clase(s) | Archivo de código | Prueba |
|---|---|---|---|---|---|---|
| RF01 | R9, R10 | `[COMPLETAR]` | — | Cliente | `[COMPLETAR]` | `[COMPLETAR]` |
| RF02 | R10, R11 | `[COMPLETAR]` | BPMN 1 | Usuario | `[COMPLETAR]` | `[COMPLETAR]` |
| RF03 | R1, R2 | `[COMPLETAR]` | — | Destino | `[COMPLETAR]` | `[COMPLETAR]` |
| RF04 | R1, R2 | `[COMPLETAR]` | — | Destino | `[COMPLETAR]` | `[COMPLETAR]` |
| RF05 | R8 | `[COMPLETAR]` | — | Destino | `[COMPLETAR]` | `[COMPLETAR]` |
| RF06 | R8 | `[COMPLETAR]` | — | Destino | `[COMPLETAR]` | `[COMPLETAR]` |
| RF07 | R8 | `[COMPLETAR]` | — | Destino, Paquete | `[COMPLETAR]` | `[COMPLETAR]` |
| RF08 | R3–R6 | `[COMPLETAR]` | BPMN 2 | Paquete, Destino | `[COMPLETAR]` | `[COMPLETAR]` |
| RF09 | R6 | `[COMPLETAR]` | BPMN 2 | Paquete | `[COMPLETAR]` | `[COMPLETAR]` |
| RF10 | R7 | `[COMPLETAR]` | BPMN 2 | Paquete | `[COMPLETAR]` | `[COMPLETAR]` |
| RF11 | S5 | `[COMPLETAR]` | — | Paquete | `[COMPLETAR]` | `[COMPLETAR]` |
| RF12 | R14, R15 | `[COMPLETAR]` | BPMN 1 | Paquete | `[COMPLETAR]` | `[COMPLETAR]` |
| RF13 | R11–R16 | `[COMPLETAR]` | BPMN 1 | Reserva | `[COMPLETAR]` | `[COMPLETAR]` |
| RF14 | R11, R17 | `[COMPLETAR]` | — | Reserva | `[COMPLETAR]` | `[COMPLETAR]` |
| RF15 | S1 | `[COMPLETAR]` | — | Reserva | `[COMPLETAR]` | `[COMPLETAR]` |
| RF16 | S2, S3 | `[COMPLETAR]` | BPMN 1 | Reserva, Administrador | `[COMPLETAR]` | `[COMPLETAR]` |
| RF17 | R17 | `[COMPLETAR]` | — | Reserva | `[COMPLETAR]` | `[COMPLETAR]` |

---

## 4. Planificación ágil (criterio 4.1.3)

### 4.1 Metodología y justificación
> **Qué va aquí:** qué marco usan (Scrum adaptado) y por qué encaja con un equipo de 2 o 3 personas y 5 días. Menciona las adaptaciones (sprints cortos de 1 a 2 días, daily de 10 minutos, etc.).

`[COMPLETAR]`

### 4.2 Product Backlog

> **Qué va aquí:** lista priorizada de historias de usuario ("Como [rol], quiero [acción], para [beneficio]"), cada una ligada a un RF. Prellené las prioritarias; escribe el texto completo de cada historia. Estimación en puntos (1, 2, 3, 5, 8).

| ID | Historia de usuario | RF | Prioridad | Puntos | Sprint |
|---|---|---|---|---|---|
| HU01 | Como administrador, quiero registrar destinos, para armar el catálogo. | RF03 | Must | `[ ]` | 1 |
| HU02 | Como administrador, quiero modificar, listar y desactivar destinos. | RF04–RF07 | Must | `[ ]` | 1 |
| HU03 | Como cliente, quiero registrarme y autenticarme. | RF01, RF02 | Must | `[ ]` | 2 |
| HU04 | Como administrador, quiero crear un paquete con precio calculado automáticamente. | RF08, RF09 | Must | `[ ]` | 2 |
| HU05 | Como administrador, quiero publicar un paquete para fijar su precio. | RF10 | Must | `[ ]` | 2 |
| HU06 | Como cliente, quiero ver paquetes con cupo disponible. | RF12 | Must | `[ ]` | 2 |
| HU07 | Como cliente, quiero reservar un paquete. | RF13 | Must | `[ ]` | 2 |
| HU08 | Como cliente, quiero ver mi historial de reservas. | RF14 | Must | `[ ]` | 2 |
| HU09 | Como administrador, quiero confirmar y consultar reservas. | RF16, RF17 | Should | `[ ]` | 3 |
| HU10 | Como cliente/administrador, quiero cancelar una reserva. | RF15 | Should | `[ ]` | 3 |
| HU11 | Como administrador, quiero modificar paquetes en borrador. | RF11 | Should | `[ ]` | 3 |
| HU12 | `[COMPLETAR: historias técnicas de seguridad y validación]` | RNF03–RNF07 | Must | `[ ]` | 2 |

### 4.3 Sprint Backlog y cronograma (5 días)

| Sprint | Días | Objetivo | Historias | Entregable | Responsable |
|---|---|---|---|---|---|
| 1 | 1–2 | Base del sistema: BD + destinos | HU01, HU02 | Esquema SQLite, CRUD de destinos, modelos | `[COMPLETAR]` |
| 2 | 3–4 | Núcleo del negocio + seguridad | HU03–HU08, HU12 | Registro/login con hash, paquetes, reservas con reglas | `[COMPLETAR]` |
| 3 | 5 | Cierre y calidad | HU09–HU11 | Funciones Should, pruebas, informe final | `[COMPLETAR]` |

**Tareas por sprint:** `[COMPLETAR: desglosa cada historia en tareas de 1 a 4 horas, con responsable]`

**Reuniones:** `[COMPLETAR: daily de 10 min, revisión al final de cada sprint]`

---

## 5. Implementación (criterio 4.1.4)

### 5.1 Arquitectura y estructura del proyecto
> **Qué va aquí:** el árbol de carpetas real del repositorio y una frase por carpeta sobre su responsabilidad (modelos, repositorios, servicios, seguridad). Justifica la separación por capas: cada capa cambia por una razón distinta.

`[COMPLETAR]`

### 5.2 Persistencia de datos
**Motor:** SQLite (módulo `sqlite3` de la librería estándar). `[COMPLETAR: justificación]`

**Tablas previstas:** `usuarios`, `destinos`, `paquetes`, `paquete_destino` (tabla intermedia N:M), `reservas`.

> **Qué va aquí:** el script SQL con las restricciones (`UNIQUE` en correo y nombre de destino, `CHECK (costo_base > 0)`, `FOREIGN KEY`), un diagrama entidad-relación simple y una explicación de por qué `paquete_destino` es necesaria.

`[COMPLETAR]`

### 5.3 Operaciones CRUD implementadas

| Entidad | Create | Read | Update | Delete |
|---|---|---|---|---|
| Destino | `[ ]` | `[ ]` | `[ ]` | `[ ]` (solo si no está en paquetes) |
| Paquete | `[ ]` | `[ ]` | `[ ]` (solo borrador) | `[COMPLETAR: decisión]` |
| Reserva | `[ ]` | `[ ]` | `[ ]` (estado) | Cancelación lógica |

### 5.4 Principios de POO aplicados (indicador 4.1.4.G.13)

| Principio | Dónde se aplica en el código | Por qué |
|---|---|---|
| Abstracción | `[COMPLETAR: por ejemplo, Usuario abstracta]` | |
| Herencia | `[COMPLETAR: Cliente y Administrador heredan de Usuario]` | |
| Polimorfismo | `[COMPLETAR]` | |
| Encapsulamiento | `[COMPLETAR: atributos privados, validación en setters]` | |

### 5.5 Instrucciones de instalación y ejecución
```bash
git clone [COMPLETAR: URL]
cd sistema-agencia-viajes
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.agencia_viajes.main
```
**Usuario administrador inicial:** `[COMPLETAR: cómo se crea, ver S7]`

---

## 6. Seguridad (criterio 4.1.5)

### 6.1 Autenticación
> **Qué va aquí:** qué librería usan (`bcrypt` o `argon2-cffi`, ambas de PyPI), cómo hashean al registrar y cómo verifican al iniciar sesión. Justifica por qué **no** SHA-256 ni MD5 (rápidos → fáciles de fuerza bruta; bcrypt es lento a propósito y trae *salt* incorporado).

`[COMPLETAR]`

### 6.2 Validación de credenciales y entradas
> **Qué va aquí:** las validaciones concretas: formato de correo, RUT con dígito verificador (módulo 11), fortaleza mínima de contraseña, mensaje genérico ante login fallido ("credenciales inválidas": nunca "el correo no existe"), consultas parametrizadas.

`[COMPLETAR]`

### 6.3 Protección de datos sensibles
> **Qué va aquí:** cómo se cumplen R10 y R17. Qué se hasheó, qué se oculta en listados y errores, y si decidieron cifrar RUT/teléfono (`cryptography` / Fernet, con la clave fuera del repositorio en una variable de entorno o `.env` ignorado por git).

`[COMPLETAR]`

### 6.4 Evaluación de seguridad con apoyo de IA (indicador 4.1.5.I.20, vale 10 %)
> **Qué va aquí:** una revisión sistemática. Sugerencia: lista de amenazas (inyección SQL, fuerza bruta, escalamiento de privilegios, exposición de datos en errores) y, para cada una, qué riesgo hay, qué hizo la IA al revisarla, **qué validaste tú con criterio técnico** y qué mejora implementaste.

| Amenaza | Riesgo en este sistema | Recomendación de IA | Mi validación técnica | Mejora aplicada |
|---|---|---|---|---|
| Inyección SQL | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| Fuerza bruta en login | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| Acceso a funciones de otro rol | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| Fuga de RUT/teléfono en errores | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| Secretos en el repositorio | `[ ]` | `[ ]` | `[ ]` | `[ ]` |

---

## 7. Uso crítico de herramientas de IA (indicador 4.1.4.I.16, vale 10 %)

> **Qué va aquí:** una bitácora **llevada desde el día 1**. La guía dice que código de IA sin análisis ni ajustes es insuficiente. Registra cada uso relevante: el prompt, lo que devolvió, qué verificaste y qué decidiste. Incluye los casos en que **descartaste** la sugerencia: valen tanto como los que aceptaste.

| # | Fecha | Herramienta | Qué pedí | Qué sugirió | Cómo lo validé | Decisión (usado / modificado / descartado) y por qué | Integrante |
|---|---|---|---|---|---|---|---|
| 1 | `[ ]` | Claude | Revisión del análisis de requerimientos y modelo de clases | Detectó contradicciones con las reglas del caso (RN02 vs R3, RN04 vs R8), sugirió herencia `Usuario` y separar servicios | Contrasté cada punto con el texto del caso | `[COMPLETAR]` | `[ ]` |
| 2 | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |

---

## 8. Pruebas

> **Qué va aquí:** pruebas de las reglas críticas con resultado esperado y obtenido. Idealmente con `pytest` o `unittest`, más capturas de la ejecución.

| Prueba | Regla | Entrada | Resultado esperado | Resultado obtenido |
|---|---|---|---|---|
| Reserva sobre el cupo | R14 | Paquete cupo 12, reservar 13 | Rechazada | `[ ]` |
| Reserva con salida vencida | R15 | Paquete con salida ayer | Rechazada | `[ ]` |
| Precio congelado | R7 | Publicar paquete, luego subir costo de un destino | Precio del paquete no cambia | `[ ]` |
| Correo duplicado | R9 | Registrar dos veces el mismo correo | Segundo rechazado | `[ ]` |
| Contraseña en BD | R10 | Inspeccionar la tabla `usuarios` | Solo hash | `[ ]` |
| Costo cero | R2 | Destino con costo 0 | Rechazado | `[ ]` |
| Paquete con 1 o 6 destinos | R3 | Crear con 1 y con 6 | Ambos rechazados | `[ ]` |
| Datos sensibles en error | R17 | Provocar un error de reserva | El mensaje no contiene RUT ni teléfono | `[ ]` |

---

## 9. Conclusiones

`[COMPLETAR: qué se logró frente a la problemática, qué quedó fuera y por qué, y qué mejorarían en una segunda versión]`

---

## Referencias

- Sánchez Palacio, A. (2025). *ChatGPT y OpenAI: desarrollo y uso de herramientas de inteligencia artificial generativa.* RA-MA Editorial.
- Jiménez de Parga, C. (2021). *UML: arquitectura de aplicaciones en Java, C++ y Python* (1.ª ed.). Ra-Ma.
- Cuevas Álvarez, A. (2016). *Python 3.* RA-MA Editorial.
- `[COMPLETAR: documentación oficial de Python, sqlite3, bcrypt en PyPI, OWASP, etc.]`
