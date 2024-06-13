# {{ subject.split('#')[-1].split('/')[-1]  }}

Uri : <{{subject}}>

{% if description %}{{ description }}{% endif %}
{% if comment %}{{ comment }}{% endif %}
{% if label %}{{ label }}{% endif %}
{% if type %}{{ type }}{% endif %}
{% if subClasses|length > 0 %}## SubClasses
{% for subClass in subClasses %}
- [{{ subClass }}](./{{ subClass.split('#')[-1] }}.md)
{% endfor %}{% endif %}
{% if superClasses|length > 0 %}## SuperClasses
{% for superClass in superClasses %}
- [{{ superClass.split('#')[-1] }}](./{{ superClass.split('#')[-1] }}.md)
{% endfor %}{% endif %}
{% if equivalentClasses|length > 0 %}## EquivalentClasses
{% for equivalentClass in equivalentClasses %}
- [{{ equivalentClass.split('#')[-1] }}](./{{ equivalentClass.split('#')[-1] }}.md)
{% endfor %}{% endif %}
{% if disjointClasses|length > 0 %}## DisjointClasses
{% for disjointClass in disjointClasses %}
- [{{ disjointClass.split('#')[-1] }}](./{{ disjointClass.split('#')[-1] }}.md)
{% endfor %}{% endif %}
{% if individuals|length > 0 %}## Individuals
{% for individual in individuals %}
- [{{ individual.split('#')[-1] }}](./{{ individual.split('#')[-1] }}.md)
{% endfor %}{% endif %}
{% if annotations|length > 0 %}## Annotations
{% for predicate, objects in annotations.items() %}
- **{{ predicate.split('#')[-1].split('/')[-1] }}**: {{ objects | join(', ') }}
{% endfor %}{% endif %}
{% if properties|length > 0 %}## Properties
{% for predicate, objects in properties.items() %}
- **{{ predicate }}**: {{ objects | join(', ') }}
{% endfor %}{% endif %}


[Back to Index](./index.md)
