# backend/agent_tools/available_tools.py
import json
from datetime import datetime
import pytz # type: ignore # Necesario para zonas horarias
from typing import Optional
import random # Para simular clima variable (¡REEMPLAZAR CON API REAL!)

# --- Funciones de Herramientas ---

def get_current_datetime(location: Optional[str] = None) -> str:
    """
    Obtiene la fecha y hora actual. Si se proporciona una ubicación (como nombre de ciudad o
    identificador de zona horaria IANA como 'Asia/Tokyo' o 'Europe/Madrid'),
    devuelve la hora en esa zona horaria. De lo contrario, devuelve la hora en UTC.
    """
    try:
        if location:
            # Intenta encontrar una zona horaria que coincida (esto es básico,
            # una implementación real podría usar geolocalización o una búsqueda más robusta)
            target_tz_str = location # Asumir que es un ID de zona válido primero
            try:
                target_tz = pytz.timezone(target_tz_str)
            except pytz.UnknownTimeZoneError:
                # Si no es un ID válido, buscar en las zonas comunes (simplificado)
                found_tz = None
                for tz_name in pytz.common_timezones:
                    if location.lower() in tz_name.lower().replace('_', ' '):
                        found_tz = tz_name
                        break
                if found_tz:
                    target_tz = pytz.timezone(found_tz)
                    print(f"Zona horaria encontrada para '{location}': {found_tz}")
                else:
                    # Si no se encuentra, devolver UTC e indicar el problema
                    print(f"Advertencia: No se encontró zona horaria para '{location}'. Devolviendo UTC.")
                    target_tz = pytz.utc

            now = datetime.now(target_tz)
        else:
            # Si no hay ubicación, usar UTC
            now = datetime.now(pytz.utc)

        return now.strftime('%Y-%m-%d %H:%M:%S %Z%z') # Formato ISO con zona horaria

    except Exception as e:
        print(f"Error en get_current_datetime para '{location}': {e}")
        # Devolver UTC en caso de error inesperado
        return datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S %Z%z') + " (Error, fallback a UTC)"


def get_current_weather(location: str, unit: Optional[str] = "celsius") -> str:
    """
    Obtiene el pronóstico del tiempo actual para una ubicación específica.
    ¡¡¡ ESTA ES UNA IMPLEMENTACIÓN DE EJEMPLO - CONECTAR A UNA API REAL !!!
    """
    print(f"ADVERTENCIA: Usando datos de clima simulados para {location}")
    # SIMULACIÓN: Reemplazar con llamada a API real (OpenWeatherMap, WeatherAPI, etc.)
    try:
        # Simular datos variables para que no sea siempre lo mismo
        temp = random.randint(-5, 35)
        conditions = ["Soleado", "Parcialmente Nublado", "Nublado", "Lluvioso", "Tormenta Eléctrica", "Nevando"]
        condition = random.choice(conditions)

        if unit == "fahrenheit":
            temp = (temp * 9/5) + 32
            unit_symbol = "F"
        else:
            unit_symbol = "C" # Default a Celsius

        result = {
            "location": location,
            "temperature": f"{temp:.0f}",
            "unit": unit,
            "condition": condition,
            "detail": f"Datos simulados. Temperatura {temp:.0f}°{unit_symbol}, condición: {condition}."
        }
        return json.dumps(result)

    except Exception as e:
        print(f"Error en simulación de get_current_weather para '{location}': {e}")
        return json.dumps({"error": f"No se pudo obtener el clima simulado para {location}", "details": str(e)})


def simple_calculator(expression: str) -> str:
    """
    Evalúa una expresión matemática simple de forma segura.
    Solo permite números, operadores +, -, *, /, y paréntesis.
    """
    import operator
    import ast

    allowed_nodes = {
        ast.Expression, ast.Add, ast.Sub, ast.Mult, ast.Div,
        ast.UnaryOp, ast.Num, ast.BinOp, ast.USub, ast.UAdd,
        # Para versiones antiguas de ast, los números pueden ser ast.Constant
        ast.Constant if hasattr(ast, 'Constant') else ast.Num
    }
    allowed_ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.UAdd: operator.pos, ast.USub: operator.neg
    }

    try:
        tree = ast.parse(expression, mode='eval')

        # Validar que solo se usen nodos permitidos
        for node in ast.walk(tree):
            if type(node) not in allowed_nodes:
                 raise ValueError(f"Operación o nodo no permitido: {type(node)}")

        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            elif isinstance(node, (ast.Num, ast.Constant)): # Handle numbers (Constant for newer Python)
                 # Asegurarse de que sea numérico (int/float)
                if not isinstance(node.n, (int, float)):
                     raise TypeError("Solo se permiten números")
                return node.n
            elif isinstance(node, ast.BinOp):
                if type(node.op) not in allowed_ops:
                    raise ValueError(f"Operador binario no permitido: {type(node.op)}")
                left = _eval(node.left)
                right = _eval(node.right)
                return allowed_ops[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp):
                if type(node.op) not in allowed_ops:
                     raise ValueError(f"Operador unario no permitido: {type(node.op)}")
                operand = _eval(node.operand)
                return allowed_ops[type(node.op)](operand)
            else:
                raise TypeError(f"Nodo no soportado: {node}")

        result = _eval(tree)
        return json.dumps({"result": result, "expression": expression})

    except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError) as e:
        print(f"Error en simple_calculator para '{expression}': {e}")
        return json.dumps({"error": f"Error al evaluar la expresión: {str(e)}", "expression": expression})
    except Exception as e:
        print(f"Error inesperado en simple_calculator para '{expression}': {e}")
        return json.dumps({"error": f"Error inesperado: {str(e)}", "expression": expression})


# --- Schemas de Herramientas (Formato OpenAI) ---

AVAILABLE_TOOLS_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "Obtiene la fecha y hora actual. Si el usuario especifica una ubicación (ciudad o zona horaria como 'Asia/Tokyo'), úsala para obtener la hora local; de lo contrario, devuelve la hora UTC.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Opcional. El nombre de la ciudad (ej. 'Londres') o el identificador de zona horaria IANA (ej. 'Europe/Paris', 'America/New_York') para obtener la hora local.",
                    },
                },
                "required": [], # Location es opcional
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Obtiene la información del clima actual para una ubicación específica proporcionada por el usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "La ciudad y estado/país para la cual obtener el clima, ej. 'San Francisco, CA' o 'Tokio, Japón'.",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "La unidad de temperatura a usar. Por defecto es 'celsius'.",
                    },
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "simple_calculator",
            "description": "Evalúa una expresión matemática simple (suma, resta, multiplicación, división).",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "La expresión matemática a evaluar, ej. '10 + 5 * (3 - 1)'",
                    },
                },
                "required": ["expression"],
            },
        },
    }
]

# --- Mapeo de Nombres a Funciones ---

TOOL_NAME_TO_FUNCTION_MAP = {
    "get_current_datetime": get_current_datetime,
    "get_current_weather": get_current_weather,
    "simple_calculator": simple_calculator,
}