"""Genera información de prueba realista y completa para una presentación
ejecutiva: los 4 niveles educativos (Preparatoria, 2 Licenciaturas, Maestría
y Doctorado), con programas, planes de estudio, materias, ciclo escolar,
grupos con horario y aula, alumnos inscritos (mínimo 3 por grupo), 18
docentes por nivel educativo, personal administrativo (incluyendo nómina) y
un directivo por nivel más el director general.

Idempotente: se puede volver a correr sin duplicar registros (usa
``get_or_create`` con claves únicas / deterministas en todos los modelos).

Uso::

    python manage.py generar_datos_demo
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.academico.models import (
    CicloEscolar,
    Grupo,
    HorarioClase,
    Materia,
    NivelEducativo,
    PlanEstudios,
    Programa,
)
from apps.alumnos.models import Alumno
from apps.core.models import Plantel, Usuario
from apps.docentes.models import AsignacionDocente, Docente
from apps.inscripciones.models import Inscripcion, InscripcionMateria
from apps.nomina.models import Empleado, Puesto

PASSWORD_DEMO = "Demo1234!"
ALUMNOS_POR_PROGRAMA = 8
DOCENTES_POR_NIVEL = 18

NOMBRES_M = [
    "Carlos", "Miguel", "Jorge", "Alejandro", "Fernando", "Ricardo", "Eduardo",
    "Javier", "Roberto", "Francisco", "Manuel", "Sergio", "Rafael", "Pedro",
    "Jose", "Luis", "Antonio", "Diego", "Andres", "Gabriel", "Arturo", "Raul",
    "Hector", "Ivan", "Adrian", "Emilio", "Ruben", "Salvador", "Victor", "Omar",
]
NOMBRES_F = [
    "Maria", "Ana", "Laura", "Patricia", "Claudia", "Veronica", "Alejandra",
    "Gabriela", "Beatriz", "Silvia", "Elena", "Carmen", "Rosa", "Isabel",
    "Daniela", "Sofia", "Adriana", "Karla", "Monica", "Paola", "Fernanda",
    "Lucia", "Teresa", "Guadalupe", "Norma", "Diana", "Andrea", "Cecilia",
]
APELLIDOS = [
    "Garcia", "Martinez", "Lopez", "Hernandez", "Gonzalez", "Perez", "Sanchez",
    "Ramirez", "Flores", "Torres", "Rivera", "Gomez", "Diaz", "Reyes",
    "Morales", "Cruz", "Ortiz", "Gutierrez", "Chavez", "Ramos", "Vazquez",
    "Castillo", "Jimenez", "Mendoza", "Ruiz", "Aguilar", "Vargas", "Herrera",
    "Medina", "Rojas", "Delgado", "Guerrero", "Rocha", "Salazar", "Cabrera",
]

AULAS = [
    "Aula 101", "Aula 102", "Aula 103", "Aula 201", "Aula 202", "Aula 203",
    "Laboratorio de Computo 1", "Laboratorio de Computo 2", "Auditorio",
    "Sala de Posgrado 1", "Sala de Posgrado 2", "Biblioteca - Sala de estudio",
]

MATERIAS_POR_PROGRAMA = {
    "PREP-GEN": [
        "Matematicas I", "Espanol I", "Quimica I", "Historia Universal",
        "Ingles I", "Informatica",
    ],
    "LIC-ADM": [
        "Fundamentos de Administracion", "Contabilidad I",
        "Matematicas Financieras", "Derecho Empresarial", "Mercadotecnia",
        "Economia I",
    ],
    "LIC-SIS": [
        "Programacion I", "Matematicas Discretas",
        "Arquitectura de Computadoras", "Bases de Datos I",
        "Algebra Lineal", "Redes de Computadoras",
    ],
    "MAE-MBA": [
        "Alta Direccion", "Finanzas Corporativas Avanzadas",
        "Marketing Estrategico", "Liderazgo Organizacional",
        "Negocios Internacionales", "Innovacion y Emprendimiento",
    ],
    "DR-EDU": [
        "Epistemologia de la Investigacion Educativa", "Seminario de Tesis I",
        "Politicas Educativas Comparadas",
        "Metodologia de la Investigacion Avanzada", "Seminario de Tesis II",
        "Filosofia de la Educacion",
    ],
}

ESPECIALIDADES_POR_NIVEL = {
    "PREP": ["Matematicas", "Ciencias Naturales", "Humanidades", "Ingles", "Informatica"],
    "LIC": ["Administracion", "Sistemas Computacionales", "Finanzas", "Mercadotecnia", "Derecho"],
    "MAE": ["Alta Direccion", "Finanzas Corporativas", "Negocios Internacionales"],
    "DR": ["Investigacion Educativa", "Politica Educativa", "Metodologia"],
}

PUESTOS_ADMINISTRATIVOS = [
    ("Coordinador Academico", Decimal("22000")),
    ("Jefe de Control Escolar", Decimal("20000")),
    ("Recursos Humanos", Decimal("18000")),
    ("Servicios Escolares", Decimal("16000")),
    ("Contabilidad", Decimal("19000")),
    ("Soporte de Sistemas", Decimal("17000")),
    ("Auxiliar de Nomina", Decimal("15000")),
    ("Jefe de Nomina", Decimal("23000")),
]


def normalizar(texto: str) -> str:
    tabla = str.maketrans("áéíóúÁÉÍÓÚñÑ", "aeiouAEIOUnN")
    return texto.translate(tabla)


def generar_rfc_ficticio(nombre: str, apellido: str, indice: int) -> str:
    letras = (normalizar(apellido)[:2] + normalizar(nombre)[:2]).upper().ljust(4, "X")
    return f"{letras}{800101 + indice:06d}{'A' + str(indice % 10)}1"[:13]


class Command(BaseCommand):
    help = "Genera datos de prueba completos (todos los niveles educativos) para una demo ejecutiva."

    def handle(self, *args, **options):
        self.rng = random.Random(42)
        self.contadores = {"docentes": 0, "alumnos": 0, "administrativos": 0, "directivos": 0}

        with transaction.atomic():
            plantel = self._crear_plantel()
            niveles = self._crear_niveles()
            ciclo = self._crear_ciclo(plantel)
            programas = self._crear_programas(plantel, niveles)
            planes = self._crear_planes(programas)
            self._crear_materias_y_grupos(planes, ciclo)
            self._crear_docentes_y_asignaciones(niveles, plantel, ciclo)
            self._crear_alumnos_e_inscripciones(programas, planes, plantel, ciclo)
            self._crear_administrativos(plantel)
            self._crear_directivos(niveles)

        self._resumen()

    # ------------------------------------------------------------- catálogos
    def _crear_plantel(self):
        plantel, _ = Plantel.objects.get_or_create(
            clave="P1",
            defaults={"nombre": "Plantel Central", "activo": True},
        )
        return plantel

    def _crear_niveles(self):
        datos = [
            ("PREP", "Preparatoria", 0),
            ("LIC", "Licenciatura", 1),
            ("MAE", "Maestria", 2),
            ("DR", "Doctorado", 3),
        ]
        niveles = {}
        for clave, nombre, orden in datos:
            nivel, _ = NivelEducativo.objects.get_or_create(
                clave=clave, defaults={"nombre": nombre, "orden": orden}
            )
            niveles[clave] = nivel
        return niveles

    def _crear_ciclo(self, plantel):
        ciclo, _ = CicloEscolar.objects.get_or_create(
            plantel=plantel,
            clave="2026-2027",
            defaults={
                "nombre": "Ciclo Escolar 2026-2027",
                "fecha_inicio": date(2026, 8, 1),
                "fecha_fin": date(2027, 7, 31),
                "activo": True,
            },
        )
        return ciclo

    def _crear_programas(self, plantel, niveles):
        definiciones = [
            ("PREP-GEN", "Bachillerato General", "PREP", 6, "Certificado de Bachillerato"),
            ("LIC-ADM", "Licenciatura en Administracion", "LIC", 9, "Licenciado en Administracion"),
            ("LIC-SIS", "Licenciatura en Sistemas Computacionales", "LIC", 9, "Ingeniero en Sistemas Computacionales"),
            ("MAE-MBA", "Maestria en Administracion de Negocios", "MAE", 4, "Maestro en Administracion de Negocios"),
            ("DR-EDU", "Doctorado en Educacion", "DR", 6, "Doctor en Educacion"),
        ]
        programas = {}
        for clave, nombre, nivel_clave, duracion, titulo in definiciones:
            programa, _ = Programa.objects.get_or_create(
                clave=clave,
                plantel=plantel,
                defaults={
                    "nombre": nombre,
                    "nivel": niveles[nivel_clave],
                    "modalidad": Programa.Modalidad.PRESENCIAL,
                    "duracion_periodos": duracion,
                    "titulo_otorga": titulo,
                },
            )
            programas[clave] = programa
        return programas

    def _crear_planes(self, programas):
        planes = {}
        for clave, programa in programas.items():
            plan, _ = PlanEstudios.objects.get_or_create(
                programa=programa,
                version="2026",
                defaults={"total_creditos": 60},
            )
            planes[clave] = plan
        return planes

    def _crear_materias_y_grupos(self, planes, ciclo):
        self.grupos_por_programa = {}
        for clave_programa, plan in planes.items():
            nombres_materias = MATERIAS_POR_PROGRAMA[clave_programa]
            grupos_programa = []
            for indice, nombre_materia in enumerate(nombres_materias, start=1):
                materia, _ = Materia.objects.get_or_create(
                    plan_estudios=plan,
                    clave=f"{clave_programa}-M{indice}",
                    defaults={
                        "nombre": nombre_materia,
                        "periodo": 1 if indice <= 3 else 2,
                        "creditos": 8,
                        "horas_teoricas": 4,
                        "horas_practicas": 2,
                        "tipo": Materia.Tipo.OBLIGATORIA,
                    },
                )
                turno = Grupo.Turno.MATUTINO if indice % 2 else Grupo.Turno.VESPERTINO
                aula_offset = sum(ord(c) for c in clave_programa)
                grupo, creado = Grupo.objects.get_or_create(
                    ciclo_escolar=ciclo,
                    materia=materia,
                    clave="A",
                    defaults={
                        "cupo_maximo": 30,
                        "aula": AULAS[(indice + aula_offset) % len(AULAS)],
                        "turno": turno,
                    },
                )
                if creado:
                    inicio = "08:00" if turno == Grupo.Turno.MATUTINO else "16:00"
                    fin = "09:30" if turno == Grupo.Turno.MATUTINO else "17:30"
                    dias = [((indice - 1) % 5) + 1, ((indice + 1) % 5) + 1]
                    for dia in dias:
                        HorarioClase.objects.get_or_create(
                            grupo=grupo, dia_semana=dia,
                            defaults={"hora_inicio": inicio, "hora_fin": fin},
                        )
                grupos_programa.append(grupo)
            self.grupos_por_programa[clave_programa] = grupos_programa

    # -------------------------------------------------------------- personas
    def _siguiente_nombre(self):
        sexo = self.rng.choice(["M", "F"])
        nombre = self.rng.choice(NOMBRES_M if sexo == "M" else NOMBRES_F)
        apellido_p = self.rng.choice(APELLIDOS)
        apellido_m = self.rng.choice(APELLIDOS)
        return nombre, f"{apellido_p} {apellido_m}", sexo

    def _crear_usuario(self, username, nombre, apellido, rol):
        usuario, creado = Usuario.objects.get_or_create(
            username=username,
            defaults={
                "first_name": nombre,
                "last_name": apellido,
                "email": f"{username}@escolar-demo.mx",
                "rol_principal": rol,
                "is_active": True,
            },
        )
        if creado:
            usuario.set_password(PASSWORD_DEMO)
            usuario.save(update_fields=["password"])
        return usuario

    def _crear_docentes_y_asignaciones(self, niveles, plantel, ciclo):
        nivel_estudios_por_nivel = {
            "PREP": Docente.NivelEstudios.LICENCIATURA,
            "LIC": Docente.NivelEstudios.MAESTRIA,
            "MAE": Docente.NivelEstudios.DOCTORADO,
            "DR": Docente.NivelEstudios.DOCTORADO,
        }
        self.docentes_por_nivel = {}
        for nivel_clave in niveles:
            docentes_nivel = []
            for i in range(1, DOCENTES_POR_NIVEL + 1):
                nombre, apellido, _sexo = self._siguiente_nombre()
                username = f"docente.{nivel_clave.lower()}{i:02d}"
                usuario = self._crear_usuario(username, nombre, apellido, Usuario.Rol.DOCENTE)
                docente, creado = Docente.objects.get_or_create(
                    usuario=usuario,
                    defaults={
                        "numero_empleado": f"DOC-{nivel_clave}-{i:02d}",
                        "especialidad": self.rng.choice(ESPECIALIDADES_POR_NIVEL[nivel_clave]),
                        "nivel_estudios": nivel_estudios_por_nivel[nivel_clave],
                        "rfc": generar_rfc_ficticio(nombre, apellido, i),
                        "curp": generar_rfc_ficticio(nombre, apellido, i) + "HDF",
                        "fecha_ingreso": date(2022, 8, 1),
                        "activo": True,
                    },
                )
                if creado:
                    docente.planteles.add(plantel)
                docentes_nivel.append(docente)
                self.contadores["docentes"] += 1
            self.docentes_por_nivel[nivel_clave] = docentes_nivel

            puesto_docente, _ = Puesto.objects.get_or_create(
                plantel=plantel,
                nombre=f"Docente {NivelEducativo.objects.get(clave=nivel_clave).nombre}",
                defaults={"sueldo_base": {
                    "PREP": Decimal("12000"), "LIC": Decimal("18000"),
                    "MAE": Decimal("25000"), "DR": Decimal("32000"),
                }[nivel_clave]},
            )
            for docente in docentes_nivel:
                Empleado.objects.get_or_create(
                    usuario=docente.usuario,
                    defaults={
                        "puesto": puesto_docente,
                        "rfc": docente.rfc,
                        "fecha_ingreso": docente.fecha_ingreso,
                        "activo": True,
                    },
                )

        # Asignar como responsables de grupo a los docentes de su mismo nivel.
        for clave_programa, grupos in self.grupos_por_programa.items():
            nivel_clave = self._nivel_de_programa(clave_programa)
            docentes_nivel = self.docentes_por_nivel[nivel_clave]
            for indice, grupo in enumerate(grupos):
                docente = docentes_nivel[indice % len(docentes_nivel)]
                AsignacionDocente.objects.get_or_create(
                    grupo=grupo,
                    docente=docente,
                    defaults={"fecha_inicio": ciclo.fecha_inicio, "activo": True},
                )

    def _nivel_de_programa(self, clave_programa: str) -> str:
        return {
            "PREP-GEN": "PREP", "LIC-ADM": "LIC", "LIC-SIS": "LIC",
            "MAE-MBA": "MAE", "DR-EDU": "DR",
        }[clave_programa]

    def _crear_alumnos_e_inscripciones(self, programas, planes, plantel, ciclo):
        for clave_programa, programa in programas.items():
            plan = planes[clave_programa]
            grupos = self.grupos_por_programa[clave_programa]
            for i in range(1, ALUMNOS_POR_PROGRAMA + 1):
                nombre, apellido, sexo = self._siguiente_nombre()
                username = f"alumno.{clave_programa.lower()}{i:02d}"
                usuario = self._crear_usuario(username, nombre, apellido, Usuario.Rol.ALUMNO)
                alumno, _ = Alumno.objects.get_or_create(
                    usuario=usuario,
                    defaults={
                        "matricula": f"{clave_programa}-{i:02d}",
                        "plantel": plantel,
                        "programa": programa,
                        "plan_estudios": plan,
                        "estatus": Alumno.Estatus.ACTIVO,
                        "fecha_ingreso": ciclo.fecha_inicio,
                        "sexo": sexo,
                        "curp": generar_rfc_ficticio(nombre, apellido, i) + "HDF",
                    },
                )
                self.contadores["alumnos"] += 1

                inscripcion, _ = Inscripcion.objects.get_or_create(
                    alumno=alumno, ciclo_escolar=ciclo,
                    defaults={"programa": programa, "estatus": Inscripcion.Estatus.INSCRITO},
                )
                for grupo in grupos:
                    InscripcionMateria.objects.get_or_create(
                        inscripcion=inscripcion, grupo=grupo,
                        defaults={"estatus": InscripcionMateria.Estatus.INSCRITO},
                    )

    def _crear_administrativos(self, plantel):
        for indice, (nombre_puesto, sueldo) in enumerate(PUESTOS_ADMINISTRATIVOS, start=1):
            puesto, _ = Puesto.objects.get_or_create(
                plantel=plantel, nombre=nombre_puesto, defaults={"sueldo_base": sueldo}
            )
            nombre, apellido, _sexo = self._siguiente_nombre()
            username = f"administrativo.{indice:02d}"
            usuario = self._crear_usuario(username, nombre, apellido, Usuario.Rol.ADMINISTRATIVO)
            Empleado.objects.get_or_create(
                usuario=usuario,
                defaults={
                    "puesto": puesto,
                    "rfc": generar_rfc_ficticio(nombre, apellido, indice),
                    "fecha_ingreso": date(2023, 1, 15),
                    "activo": True,
                },
            )
            self.contadores["administrativos"] += 1

    def _crear_directivos(self, niveles):
        for nivel_clave in niveles:
            nombre, apellido, _sexo = self._siguiente_nombre()
            username = f"directivo.{nivel_clave.lower()}"
            self._crear_usuario(username, nombre, apellido, Usuario.Rol.DIRECTIVO)
            self.contadores["directivos"] += 1
        nombre, apellido, _sexo = self._siguiente_nombre()
        self._crear_usuario("director.general", nombre, apellido, Usuario.Rol.DIRECTIVO)
        self.contadores["directivos"] += 1

    # --------------------------------------------------------------- resumen
    def _resumen(self):
        self.stdout.write(self.style.SUCCESS("Datos de prueba generados/actualizados correctamente."))
        self.stdout.write(f"Docentes: {self.contadores['docentes']}")
        self.stdout.write(f"Alumnos: {self.contadores['alumnos']}")
        self.stdout.write(f"Administrativos/nomina: {self.contadores['administrativos']}")
        self.stdout.write(f"Directivos (4 de nivel + 1 director general): {self.contadores['directivos']}")
        self.stdout.write(f"Contrasena de todas las cuentas nuevas: {PASSWORD_DEMO}")
