"""Funciones genéricas que hacen posible reutilizar un único par de vistas
(list/form) para los 28 modelos registrados en ``apps/panel/registry.py``,
replicando cómo Django admin resuelve ``list_display``/``list_filter``.
"""
from django.db import models


def resolver_valor(obj, nombre: str):
    """Obtiene el valor a mostrar en una columna, igual que hace el admin
    de Django con ``list_display`` (soporta ``__str__``, atributos,
    propiedades y métodos sin argumentos)."""
    if nombre == "__str__":
        return str(obj)
    valor = getattr(obj, nombre, None)
    if callable(valor):
        valor = valor()
    return valor


def etiqueta_campo(model, nombre: str) -> str:
    """Encabezado de columna legible para ``nombre`` (usa verbose_name del
    campo del modelo cuando existe)."""
    if nombre == "__str__":
        return model._meta.verbose_name.title()
    try:
        campo = model._meta.get_field(nombre)
        return str(campo.verbose_name).capitalize()
    except Exception:
        return nombre.replace("_", " ").replace("get ", "").capitalize()


def construir_filas(objetos, list_display):
    """Para cada objeto arma la lista de valores ya resueltos, marcando los
    booleanos para que el template los pinte como ícono (igual que el
    ``@admin.display(boolean=True)`` del admin de Django)."""
    filas = []
    for obj in objetos:
        valores = []
        for nombre in list_display:
            valor = resolver_valor(obj, nombre)
            valores.append({"valor": valor, "es_bool": isinstance(valor, bool)})
        filas.append({"obj": obj, "valores": valores})
    return filas


def resolver_campo_relacionado(model, ruta: str):
    """Recorre una ruta tipo ``programa__nivel`` (igual que un lookup de
    Django ORM) y devuelve el último campo y el modelo al que apunta,
    para poder construir las opciones de un filtro."""
    actual = model
    campo = None
    for parte in ruta.split("__"):
        campo = actual._meta.get_field(parte)
        if campo.is_relation:
            actual = campo.related_model
        else:
            break
    return campo, actual


def construir_filtros(model, list_filter, get_params):
    """Construye la definición de cada filtro (opciones + valor seleccionado)
    y el diccionario de lookups ya listo para pasar a ``queryset.filter()``."""
    filtros = []
    lookups_activos = {}
    for ruta in list_filter:
        campo, modelo_relacionado = resolver_campo_relacionado(model, ruta)
        valor_actual = get_params.get(ruta, "")

        if campo.is_relation:
            opciones = [(str(o.pk), str(o)) for o in modelo_relacionado.objects.all()]
        elif getattr(campo, "choices", None):
            opciones = [(str(clave), etiqueta) for clave, etiqueta in campo.choices]
        elif isinstance(campo, models.BooleanField):
            opciones = [("True", "Sí"), ("False", "No")]
        else:
            opciones = []

        filtros.append(
            {
                "nombre": ruta,
                "etiqueta": str(campo.verbose_name).capitalize(),
                "opciones": opciones,
                "valor": valor_actual,
            }
        )

        if valor_actual:
            if isinstance(campo, models.BooleanField) and not campo.is_relation:
                lookups_activos[ruta] = valor_actual == "True"
            else:
                lookups_activos[ruta] = valor_actual

    return filtros, lookups_activos
