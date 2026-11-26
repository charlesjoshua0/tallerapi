"""
API de Inscripciones -- Pasos 2, 3 y 4

Levántala con:
    uvicorn app.main:app --reload
y abre http://127.0.0.1:8000/docs  (ahí ves y pruebas todo lo que vayas haciendo)

El endpoint 1 (GET /cursos) ya está resuelto: úsalo de modelo para los demás.
Las funciones 2 a 5 ya existen, pero todavía NO son endpoints: les falta el decorador.

  Paso 2  ->  TODO(Paso 2): ponle a cada función su decorador @app.<método>("<ruta>", ...)
  Paso 3  ->  TODO(Paso 3): completa las reglas de cupos, prerrequisitos, duplicados y estados
  Paso 4  ->  TODO(Paso 4): documenta cada endpoint (tags, summary y responses)

Errores: siempre  raise HTTPException(status_code=..., detail="CODIGO")
Ejemplo de errores documentados para el Paso 4:
    responses={404: {"model": Error, "description": "NO_ENCONTRADO"}}
"""
from fastapi import FastAPI, HTTPException

from app import datos
from app.modelos import CambioEstado, Curso, Error, EstadoInscripcion, Inscripcion, InscripcionCrear  # noqa: F401

app = FastAPI(
    title="API de Inscripciones",
    version="1.0.0",
    description="Inscripciones académicas con control de cupos, prerrequisitos y duplicados.",
)


def _curso_json(c: dict) -> dict:
    return {**c, "cupos_disponibles": c["cupos"] - len(datos.activas_del_curso(c["codigo"]))}


# 1 --- GET /cursos  (EJEMPLO RESUELTO) ----------------------------------------
@app.get(
    "/cursos",
    response_model=list[Curso],
    tags=["Cursos"],
    summary="Listar cursos con sus cupos disponibles",
)
def listar_cursos():
    return [_curso_json(c) for c in datos.CURSOS.values()]


# 2 --- POST /inscripciones ----------------------------------------------------
@app.post(
    "/inscripciones",
    response_model=Inscripcion,
    status_code=201,
    tags=["Inscripciones"],
    summary="Inscribir a un estudiante en un curso",
    responses={
        404: {"model": Error, "description": "NO_ENCONTRADO: el estudiante o el curso no existe"},
        409: {"model": Error, "description": "DUPLICADA, PRERREQUISITOS_PENDIENTES o SIN_CUPO"},
    },
)
def crear_inscripcion(cuerpo: InscripcionCrear):
    estudiante = datos.ESTUDIANTES.get(cuerpo.estudiante_id)
    curso = datos.CURSOS.get(cuerpo.curso_codigo)
    if estudiante is None or curso is None:
        raise HTTPException(status_code=404, detail="NO_ENCONTRADO")

    # Regla 1: el estudiante no puede tener ya una inscripción activa en el curso
    if datos.buscar_activa(cuerpo.estudiante_id, cuerpo.curso_codigo) is not None:
        raise HTTPException(status_code=409, detail="DUPLICADA")

    # Regla 2: debe haber aprobado todos los prerrequisitos del curso
    if any(p not in estudiante["aprobados"] for p in curso["prerrequisitos"]):
        raise HTTPException(status_code=409, detail="PRERREQUISITOS_PENDIENTES")

    # Regla 3: debe quedar cupo (solo cuentan las inscripciones activas)
    if len(datos.activas_del_curso(cuerpo.curso_codigo)) >= curso["cupos"]:
        raise HTTPException(status_code=409, detail="SIN_CUPO")

    return datos.guardar_inscripcion(cuerpo.estudiante_id, cuerpo.curso_codigo,
                                     EstadoInscripcion.ACTIVA.value)


# 3 --- GET /inscripciones/{inscripcion_id} ------------------------------------
@app.get(
    "/inscripciones/{inscripcion_id}",
    response_model=Inscripcion,
    tags=["Inscripciones"],
    summary="Consultar una inscripción",
    responses={404: {"model": Error, "description": "NO_ENCONTRADO"}},
)
def obtener_inscripcion(inscripcion_id: int):
    inscripcion = datos.INSCRIPCIONES.get(inscripcion_id)
    if inscripcion is None:
        raise HTTPException(status_code=404, detail="NO_ENCONTRADO")
    return inscripcion


# 4 --- GET /estudiantes/{estudiante_id}/inscripciones -------------------------
@app.get(
    "/estudiantes/{estudiante_id}/inscripciones",
    response_model=list[Inscripcion],
    tags=["Estudiantes"],
    summary="Listar las inscripciones de un estudiante (activas y canceladas)",
    responses={404: {"model": Error, "description": "NO_ENCONTRADO"}},
)
def inscripciones_de_estudiante(estudiante_id: str):
    if estudiante_id not in datos.ESTUDIANTES:
        raise HTTPException(status_code=404, detail="NO_ENCONTRADO")
    return datos.del_estudiante(estudiante_id)


# 5 --- PATCH /inscripciones/{inscripcion_id} ----------------------------------
@app.patch(
    "/inscripciones/{inscripcion_id}",
    response_model=Inscripcion,
    tags=["Inscripciones"],
    summary="Cancelar una inscripción (ACTIVA -> CANCELADA)",
    responses={
        404: {"model": Error, "description": "NO_ENCONTRADO"},
        409: {"model": Error, "description": "TRANSICION_INVALIDA"},
    },
)
def cambiar_estado(inscripcion_id: int, cuerpo: CambioEstado):
    inscripcion = datos.INSCRIPCIONES.get(inscripcion_id)
    if inscripcion is None:
        raise HTTPException(status_code=404, detail="NO_ENCONTRADO")

    # Única transición válida: ACTIVA -> CANCELADA
    if (inscripcion["estado"] != EstadoInscripcion.ACTIVA.value
            or cuerpo.estado != EstadoInscripcion.CANCELADA):
        raise HTTPException(status_code=409, detail="TRANSICION_INVALIDA")

    inscripcion["estado"] = EstadoInscripcion.CANCELADA.value
    return inscripcion
