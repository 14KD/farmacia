"""
utils/validators.py — Validaciones reutilizables de teléfono y dirección.

Pensado para números de República Dominicana: código de área (809/829/849)
+ 7 dígitos = 10 dígitos en total. También acepta el código de país +1
(11 dígitos) y separadores comunes (espacios, guiones, paréntesis, +).
"""
import re

DR_AREA_CODES = ("809", "829", "849")


def clean_phone_digits(phone: str) -> str:
    """Devuelve solo los dígitos del teléfono, sin el 1 de código de país si aplica."""
    digits = re.sub(r"[^0-9]", "", phone or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def validate_phone(phone: str, required: bool = False):
    """
    Valida un teléfono dominicano.
    Retorna (ok: bool, mensaje_error: str | None).
    Un teléfono vacío se considera válido salvo que required=True.
    """
    phone = (phone or "").strip()
    if not phone:
        if required:
            return False, "El teléfono es obligatorio."
        return True, None

    if not re.match(r'^[0-9\s\+\-\(\)]+$', phone):
        return False, "El teléfono solo puede contener números, espacios, +, - y paréntesis."

    digits = clean_phone_digits(phone)
    if len(digits) != 10:
        return False, "El teléfono debe tener 10 dígitos (código de área + número), ej. 809-555-1234."
    if digits[:3] not in DR_AREA_CODES:
        return False, "El código de área no es válido. Debe iniciar con 809, 829 u 849."
    return True, None


def validate_address(address: str, required: bool = True, min_length: int = 6):
    """
    Valida una dirección. Retorna (ok: bool, mensaje_error: str | None).
    Por defecto es obligatoria y debe tener contenido real (no solo espacios
    o un par de caracteres sueltos).
    """
    address = (address or "").strip()
    if not address:
        if required:
            return False, "La dirección es obligatoria."
        return True, None
    if len(address) < min_length:
        return False, f"La dirección parece incompleta (mínimo {min_length} caracteres)."
    return True, None
