"""Formularios del Panel Ejecutivo.

Para casi todos los modelos basta ``modelform_factory(model, fields="__all__")``:
Django excluye automáticamente los campos con ``editable=False`` (por ejemplo
``clave_api``, ``neto``, los ``auto_now_add``), igual que hace el admin con
sus ``readonly_fields``. El único caso especial es ``Usuario``, porque su
campo ``password`` sí es editable a nivel modelo y jamás debe exponerse en un
formulario genérico como texto plano.
"""
from django import forms
from django.contrib.auth.password_validation import validate_password

from apps.core.models import Usuario

from .registry import PanelModelConfig


def obtener_form_class(config: PanelModelConfig):
    if config.model is Usuario:
        return UsuarioPanelForm
    return forms.modelform_factory(
        config.model,
        fields="__all__",
        exclude=config.form_exclude or None,
    )


class UsuarioPanelForm(forms.ModelForm):
    """La contraseña NUNCA se maneja como texto plano genérico: se gestiona
    aparte y se hashea con ``set_password``. Al crear un usuario nuevo sin
    especificar contraseña, queda inutilizable (``set_unusable_password``)
    hasta que un administrador se la asigne desde el admin de Django."""

    nueva_contrasena = forms.CharField(
        label="Nueva contraseña",
        required=False,
        widget=forms.PasswordInput,
        help_text="Déjalo en blanco para no cambiarla (o, si es un usuario nuevo, para dejarla sin definir).",
    )

    class Meta:
        model = Usuario
        fields = (
            "username", "first_name", "last_name", "email", "telefono", "foto",
            "rol_principal", "planteles", "is_active", "is_staff",
        )

    def clean_nueva_contrasena(self):
        valor = self.cleaned_data.get("nueva_contrasena")
        if valor:
            validate_password(valor, self.instance)
        return valor

    def save(self, commit=True):
        usuario = super().save(commit=False)
        contrasena = self.cleaned_data.get("nueva_contrasena")
        if contrasena:
            usuario.set_password(contrasena)
        elif usuario.pk is None:
            usuario.set_unusable_password()
        if commit:
            usuario.save()
            self.save_m2m()
        return usuario
