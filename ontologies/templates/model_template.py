
from pydantic import BaseModel, Field

class {{ subject.split("/")[-1].split("#")[-1] }}(BaseModel):
    {% for predicate, objects in properties.items() %}
    {{ predicate }}: Field({{ objects | join(', ') }})
    {% endfor %}

