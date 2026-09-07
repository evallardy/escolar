"""Completa el historial de cardex de los alumnos de la demo ejecutiva a
partir de las materias en las que ya están inscritos: las del periodo 1 del
plan de estudios se marcan como acreditadas (con calificación) y las del
periodo 2 en curso, para poder mostrar el módulo de Cardex con información
real y consistente con las inscripciones.

Idempotente (usa ``update_or_create``): se puede volver a correr sin
duplicar ni descuadrar datos.

Uso::

    python manage.py completar_cardex_demo
"""
import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.alumnos.models import Cardex
from apps.inscripciones.models import InscripcionMateria

CALIFICACIONES_POSIBLES = [Decimal(v) for v in ("7.5", "8.0", "8.5", "9.0", "9.5", "10.0")]


class Command(BaseCommand):
    help = "Completa Cardex e InscripcionMateria (acreditadas/cursando) para la demo ejecutiva."

    def handle(self, *args, **options):
        rng = random.Random(7)
        actualizados = {"acreditadas": 0, "cursando": 0}

        with transaction.atomic():
            registros = InscripcionMateria.objects.select_related(
                "inscripcion__alumno", "grupo__materia", "grupo__ciclo_escolar"
            )
            for inscripcion_materia in registros:
                alumno = inscripcion_materia.inscripcion.alumno
                grupo = inscripcion_materia.grupo
                materia = grupo.materia

                if materia.periodo == 1:
                    calificacion = rng.choice(CALIFICACIONES_POSIBLES)
                    inscripcion_materia.estatus = InscripcionMateria.Estatus.ACREDITADA
                    inscripcion_materia.calificacion_final = calificacion
                    inscripcion_materia.save(update_fields=["estatus", "calificacion_final"])

                    Cardex.objects.update_or_create(
                        alumno=alumno, materia=materia, intento=1,
                        defaults={
                            "grupo": grupo,
                            "ciclo_escolar": grupo.ciclo_escolar,
                            "calificacion": calificacion,
                            "estatus": Cardex.Estatus.APROBADA,
                            "creditos_obtenidos": materia.creditos,
                        },
                    )
                    actualizados["acreditadas"] += 1
                else:
                    Cardex.objects.update_or_create(
                        alumno=alumno, materia=materia, intento=1,
                        defaults={
                            "grupo": grupo,
                            "ciclo_escolar": grupo.ciclo_escolar,
                            "calificacion": None,
                            "estatus": Cardex.Estatus.CURSANDO,
                            "creditos_obtenidos": 0,
                        },
                    )
                    actualizados["cursando"] += 1

        self.stdout.write(self.style.SUCCESS("Cardex actualizado correctamente."))
        self.stdout.write(f"Materias acreditadas (periodo 1): {actualizados['acreditadas']}")
        self.stdout.write(f"Materias cursando (periodo 2): {actualizados['cursando']}")
        self.stdout.write(f"Total registros de cardex: {Cardex.objects.count()}")
