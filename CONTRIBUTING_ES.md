Política de idioma del proyecto - Español

Este repositorio usa el castellano como idioma preferido para:

- Mensajes de commit.
- Comentarios en el código fuente (cuando sean necesarios y útiles).
- Documentación, issues y PR descriptions.

Guía breve para mensajes de commit:
- Use frases cortas y en imperativo: "Corrige cálculo de nubosidad".
- Indique el alcance: archivo o módulo afectado al inicio si procede.
- Si incluye referencias a tickets, añádalas al final.

Plantilla de commit recomendada (archivo `git_commit_template_es.txt`):
1 línea título (imperativo, resumen):

Cuerpo opcional: detalle breve de la implementación y razones.

Footer opcional: referencias o notas de compatibilidad.

Cómo activar la plantilla localmente:

1. Coloque `git_commit_template_es.txt` en la raíz del repo.
2. Ejecute:

```bash
git config commit.template .git_commit_template_es.txt
```

Comentarios en el código:
- Prefiera comentarios en castellano.
- Sea claro y conciso; mantenga los comentarios explicativos y no redundantes.

Si colabora con equipos que usan otro idioma, mantenga la consideración: priorice español dentro de este repositorio, y añada traducciones sólo si es necesario para integración externa.