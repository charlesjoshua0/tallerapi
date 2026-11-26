# Paso 6: Cliente HTTP (Postman)

Las 9 peticiones del Paso 6 se probaron con Postman (versión de escritorio).

| Archivo | Qué es |
|---------|--------|
| `inscripciones.postman_collection.json` | Colección exportada de Postman con las 9 peticiones en orden. Usa las variables `base_url` (`http://127.0.0.1:8000`) e `inscripcion_id`, que se guarda en la petición 1 y se usa en la 6 y en la 8. Cada petición tiene su verificación del código de respuesta. |
| `postman-resultados-1.png` | Resultado del Runner de Postman, peticiones 1 a 7. Resumen: 14 tests, 14 pasados, 0 fallidos. |
| `postman-resultados-2.png` | Resultado del Runner de Postman, peticiones 4 a 9. |
| `postman-log-servidor.png` | Terminal de uvicorn recibiendo las 9 peticiones con sus códigos (201, 409, 409, 201, 409, 200, 200, 200, 200). |

## Cómo repetir la prueba

1. Levantar la API: `uvicorn app.main:app --reload`. Si ya estaba corriendo, reiniciarla, porque los datos están en memoria.
2. En Postman: Import → `inscripciones.postman_collection.json`.
3. Abrir la colección y darle **Run**.
