import json
from typing import Type, TypeVar, Optional, Tuple, Any
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

def validate_response_schema(raw_content: str, schema_class: Type[T]) -> Tuple[Optional[T], bool, str]:
    """
    Enforces strict Pydantic schema validation on structured LLM outputs.
    Parses raw string (handling optional markdown json fences).
    Returns:
        (parsed_instance: Optional[T], is_valid: bool, error_message: str)
    """
    cleaned = raw_content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        instance = schema_class.model_validate(data)
        return instance, True, "Success"
    except json.JSONDecodeError as e:
        return None, False, f"JSONDecodeError: {str(e)}"
    except ValidationError as e:
        return None, False, f"SchemaValidationError: {str(e)}"
    except Exception as e:
        return None, False, f"UnexpectedError: {str(e)}"
