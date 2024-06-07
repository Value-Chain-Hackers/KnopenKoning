# {{ subject }}

## SubClasses
{% for subClass in subClasses %}
- [{{ subClass }}](./{{ subClass.split('#')[-1] }}.md)
{% endfor %}

## SuperClasses
{% for superClass in superClasses %}
- [{{ superClass.split('#')[-1] }}](./{{ superClass.split('#')[-1] }}.md)
{% endfor %}

## Annotations
{% for predicate, objects in annotations.items() %}
- **{{ predicate.split('#')[-1].split('/')[-1] }}**: {{ objects | join(', ') }}
{% endfor %}

## Properties
{% for predicate, objects in properties.items() %}
- **{{ predicate }}**: {{ objects | join(', ') }}
{% endfor %}

## Axioms


[Back to Index](./index.md)
