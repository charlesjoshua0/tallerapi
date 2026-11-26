# Diseño de la API de Inscripciones

Estudiante: Carlos Daniel Albarracin Cruz

## Paso 1 — Recursos

Un recurso es un **sustantivo** que la API expone con su propia URI.
La fila de *Curso* ya está hecha como ejemplo.

| Recurso     | URI de la colección | Atributos clave                                          | Se relaciona con      |
|-------------|---------------------|----------------------------------------------------------|-----------------------|
| Curso       | `/cursos`           | codigo, nombre, cupos, prerrequisitos                    | Inscripción           |
| Estudiante  | `/estudiantes`      | id, nombre, aprobados                                    | Inscripción           |
| Inscripción | `/inscripciones`    | id, estudiante_id, curso_codigo, estado, creada_en       | Estudiante y Curso    |

Las inscripciones de un estudiante también se pueden ver como subcolección:
`/estudiantes/{estudiante_id}/inscripciones`.

**Pregunta:** "inscribir" es un verbo. ¿Por qué en REST lo modelamos como el
recurso *Inscripción* y no como una URI `/inscribir`?

> Respuesta: En REST la URI nombra una cosa y el método HTTP dice qué se hace
> con ella. Si inscribir es crear una inscripción, basta con `POST /inscripciones`.
> Una URI como `/inscribir` mete la acción en la ruta y deja el método sin
> significado, y después habría que inventar `/cancelarInscripcion`,
> `/consultarInscripcion` y así para cada operación. Además, la inscripción
> tiene datos propios (id, estado, fecha) que se necesitan consultar y modificar
> después. Si es un recurso, tiene su URI `/inscripciones/{id}` y se puede
> pedir con GET o cambiar con PATCH igual que cualquier otro.

**Para discutir en grupo.** El recurso que relaciona a Estudiante con Curso es
Inscripción: guarda `estudiante_id` y `curso_codigo`. Los cupos son un atributo
del Curso, y los cupos disponibles se calculan restando las inscripciones
activas de ese curso. Los cursos aprobados se guardan en el Estudiante, en la
lista `aprobados`.

## Paso 2 — Contrato: los 5 endpoints

Completa el código de éxito y los errores posibles de cada endpoint.
Pistas: crear → `201`; no existe → `404`; choca con una regla de negocio → `409`.

| # | Método | URI                                      | Cuerpo que recibe     | Éxito | Errores |
|---|--------|------------------------------------------|-----------------------|-------|---------|
| 1 | GET    | `/cursos`                                | —                     | 200   | —       |
| 2 | POST   | `/inscripciones`                         | `InscripcionCrear`    | 201   | 404 `NO_ENCONTRADO` (estudiante o curso); 409 `DUPLICADA`, `PRERREQUISITOS_PENDIENTES`, `SIN_CUPO`; 422 cuerpo inválido |
| 3 | GET    | `/inscripciones/{inscripcion_id}`        | —                     | 200   | 404 `NO_ENCONTRADO` |
| 4 | GET    | `/estudiantes/{estudiante_id}/inscripciones` | —                 | 200   | 404 `NO_ENCONTRADO` (estudiante) |
| 5 | PATCH  | `/inscripciones/{inscripcion_id}`        | `CambioEstado`        | 200   | 404 `NO_ENCONTRADO`; 409 `TRANSICION_INVALIDA`; 422 estado que no existe |

**Para discutir en grupo: ¿por qué cancelar es PATCH y no DELETE?** Cancelar
cambia un campo de la inscripción (`estado`); la inscripción sigue existiendo.
DELETE la borraría, y con ella se iría el registro de que el estudiante estuvo
inscrito, cuándo se inscribió y que luego canceló. Ese historial sirve para
auditoría, para reportes de deserción y para responder reclamos. Con PATCH el
cupo se libera igual, porque solo cuentan las inscripciones ACTIVAS.

## Paso 3 — Estados de una inscripción

```
   POST /inscripciones            PATCH {"estado": "CANCELADA"}
  ─────────────────────▶  ACTIVA  ──────────────────────────────▶  CANCELADA
```

**Pregunta:** ¿Qué debe responder la API si alguien intenta cancelar una
inscripción que ya está CANCELADA? ¿Por qué?

> Respuesta: `409 Conflict` con `{"detail": "TRANSICION_INVALIDA"}`. La petición
> está bien formada y la inscripción existe, así que no corresponde 400 ni 404.
> Lo que falla es que choca con el estado actual del recurso: desde CANCELADA
> no hay ninguna transición permitida. Responder 200 como si nada haría creer al
> cliente que su petición cambió algo, cuando en realidad la inscripción ya
> estaba cancelada desde antes.

**Para discutir en grupo.** Una inscripción cancelada no se borra por lo mismo
que se explicó en el Paso 2: queda como historial y ya no ocupa cupo, así que
borrarla no aporta nada. Un duplicado responde 409 y no 400 porque el JSON que
llega es válido; el problema es que entra en conflicto con algo que ya está
guardado (una inscripción activa del mismo estudiante en el mismo curso). El
400 se reserva para peticiones mal formadas, y en esta API ese caso lo cubre el
422 que devuelve FastAPI cuando el cuerpo no cumple el esquema.

## Paso 4 — Discusión sobre OpenAPI

Con `openapi.json` otro equipo puede saber qué rutas hay, qué JSON enviar, qué
devuelve cada una y qué códigos de error esperar. Le faltaría lo que no está en
el esquema: qué estudiantes y cursos existen, el orden en que se revisan las
reglas (primero duplicado, luego prerrequisitos, luego cupo), que cancelar
libera el cupo, y que los datos se pierden al reiniciar el servidor.

## Paso 6 — Discusión sobre el cliente HTTP

Las pruebas de pytest llaman a la API desde Python, sin pasar por la red.
Probar desde Postman revisa la API como la ve un cliente real: servidor
corriendo, JSON por HTTP, y una secuencia de peticiones que dependen unas de
otras (el id de la petición 1 se usa en la 6 y en la 8). La colección también
sirve a otras personas del equipo: el frontend puede ver ejemplos de
respuestas, QA puede repetir la secuencia y quien llegue nuevo puede entender
la API sin leer el código.

## Pregunta para el grupo (Entrega)

En el proyecto de mi grupo, ¿qué recurso tiene estados como la inscripción y
qué reglas podrían responder 409?

> Respuesta: En VetCare, el proyecto de mi grupo (sistema de gestión para una
> clínica veterinaria), el
> recurso que más se parece a la inscripción es la Cita. El dueño de la
> mascota la solicita y queda en estado PENDIENTE. Luego la recepcionista la
> confirma (CONFIRMADA) o la cancela, y cuando se atiende la consulta pasa a
> COMPLETADA. Igual que con la inscripción, una cita cancelada no se borra:
> se cambia su estado con PATCH y queda en el historial.
>
> Reglas que responderían 409:
>
> - Asignar un consultorio o un veterinario que ya está reservado en esa
>   franja horaria (doble reserva). Es el equivalente a SIN_CUPO.
> - Confirmar o cancelar una cita que no está PENDIENTE, por ejemplo una que
>   ya se canceló. Es el mismo caso de TRANSICION_INVALIDA.
> - Registrar una prescripción o un consumo de insumos por más unidades de
>   las que quedan en el lote, porque el stock no puede quedar negativo.
> - Hospitalizar un paciente en una jaula que no está libre.
