from rdflib import Graph, RDF, RDFS, OWL, URIRef
import os
import rdflib
from jinja2 import Environment, FileSystemLoader

class GraphProperty():
    def __init__(self, uri, label = None, comment = None, range = None):
        self.uri = uri
        self.label = label
        self.comment = comment
        self.range = range

class GraphRelation():
    def __init__(self, uri, label = None, comment = None, target = None):
        self.uri = uri
        self.label = label
        self.comment = comment
        self.target = target

class GraphClass():
    subClassOf = []
    properties: list[GraphProperty] = []
    relations: list[GraphRelation] = []
    def __init__(self, uri, label, comment = None):
        self.uri = uri
        self.label = label
        self.comment = comment


class GraphVisitor():
    def __init__(self) -> None:
        self.graph = Graph()

    def get_short_name(self, full_name, namespaces = None) -> str:
        if(not namespaces):
            namespaces = self.graph.namespaces()

        for prefix, uri in namespaces:
            if uri in full_name:
                return full_name.replace(uri, f"{prefix}:")
        return full_name


    def get_label(self, subject):
        for _, _, o1 in self.graph.triples((subject, RDFS.label, None)):
            if(o1.language == "en" or not o1.language):
                return f"{o1}"
        return self.get_short_name(subject)
    
    def get_comment(self, subject):
        for _, _, o1 in self.graph.triples((subject, RDFS.comment, None)):
            if(o1.language == "en" or not o1.language):
                return f"{o1}"
    
    def build_class(self, subject) -> GraphClass:
        comment = self.get_comment(subject)
        classLabel = self.get_label(subject)
        gClass = GraphClass(subject, classLabel, comment)
        gClass.properties = self.build_properties(subject)
        gClass.relations = self.build_relations(subject)
        return gClass

    def build_properties(self, subject):
        properties = []
        for prop, _, _ in self.graph.triples((None, RDFS.domain, subject)):
            for _, _, range_ in self.graph.triples((prop, RDFS.range,  None)):
                range_name = self.get_short_name(range_)
                properties.append(GraphProperty(prop, self.get_label(prop), self.get_comment(prop), range_name))
        return properties
    

    def build_relations(self, subject):
        relations = []
        for prop, x, range_ in self.graph.triples((None, RDFS.range, subject)):
            for (o3, p3, s3) in self.graph.triples((prop, RDFS.domain, None)):
                relations.append(GraphRelation(s3,self.get_label(s3), self.get_comment(prop),self.get_label(subject)))
        return relations

    def render_class_diagram(self, gClass):
        diagram = f"\tclass {gClass.label}{{\n"
        for prop in gClass.properties:
            diagram += f"\t\t{prop.label}\n"
        diagram += f"\t}}\n\n"
        return diagram

    def parse(self, rdf_file, format="xml"):
        self.graph.parse(rdf_file, format=format)

    def get_properties_of_class(self, class_uri):
        properties = set()

        def recurse(current_class):
            # Get properties where current_class is the domain
            for prop in self.graph.subjects(RDFS.domain, current_class):
                properties.add(prop)

            # Recurse upwards in the hierarchy
            for parent_class in self.graph.objects(current_class, RDFS.subClassOf):
                recurse(parent_class)

        # Start recursion from the given class
        recurse(class_uri)
        
        return properties

    def rdf_to_markdown(self):
        # get the namespaces in the graph
        namespaces = ""
        for prefix, uri in self.graph.namespaces():
            namespaces += f"@prefix {prefix}: <{uri}> .\n"
        
        markdown = ""
        # for each class create a markdown table with the properties
        for s, p, o in self.graph.triples((None, RDF.type, None)):
            # get if type is class or property
            type = "Unknown"
            if p == RDF.type:
                if o == OWL.Class or o == RDFS.Class:
                    type = "Class"
            if type != "Class":
                continue
            
            gClass = self.build_class(s)

            subclass= None
            for s1, p1, o1 in self.graph.triples((s, RDFS.subClassOf, None)):
                subclass = self.build_class(o1)

            markdown += f"## {gClass.label.strip(':')}\n\n"
           
            markdown += f"\t{gClass.comment}\n\n"
            markdown += f"URI : `{self.get_short_name(s)}`\n\n"
            
            if subclass:
                markdown += f"`{self.get_short_name(s)}` is a sub class of `{self.get_short_name(subclass.uri)}`\n\n"

            diagram = self.render_class_diagram(gClass)
            if(subclass):
                diagram += f"{subclass.label} --> {gClass.label} : sub class \n"
                diagram += self.render_class_diagram(subclass)
            markdown += f"```mermaid\nclassDiagram\n\tdirection RL\n{diagram}```\n\n"

            if(len(gClass.properties) > 0):
            # Get all properties where the range or domain is the current class
                properties = f"\n**Properties**\n"
                for prop in gClass.properties:
                    properties += f"* **`{prop.label}`**  ({prop.range})\n\n\t{prop.comment} \n"
                markdown += f"{properties}\n\n"
            if(len(gClass.relations) > 0):
                relations = f"\n**Relations**\n"
                for relation in gClass.relations:
                    relations += f"* **`{relation.label}`** --> `{relation.target}` \n\n\t {relation.comment}\n"
                markdown += f"{relations}\n\n"

        return markdown

class GraphRenderer():
    def __init__(self, graph):
        self.graph = graph

    def render(self):
        # Load ontology data

        # Extract subjects, their properties, and annotations
        subjects = {}
        for s in self.graph.subjects():
            subjects[s] = {
                'subClasses': list(self.graph.objects(s, RDFS.subClassOf)),
                'superClasses': list(self.graph.subjects(RDFS.subClassOf, s)),
                'annotations': {p: list(self.graph.objects(s, p)) for p in self.graph.predicates(s, None)},
                'properties': {p: list(self.graph.objects(s, p)) for p in self.graph.predicates(s, RDF.Property)},
                URIRef :URIRef
            }

        # Create output directory
        output_dir = 'docs/ontology'
        os.makedirs(output_dir, exist_ok=True)

        # Initialize Jinja2 environment
        env = Environment(loader=FileSystemLoader('ontologies/templates'))

        # Create a documentation page for each subject
        for subject, details in subjects.items():
            template = env.get_template('subject_template.md')
            rendered = template.render(
                subject=subject,
                subClasses=details['subClasses'],
                superClasses=details['superClasses'],
                annotations=details['annotations'],
                properties=details['properties']
            )
            # Save the rendered Markdown to a file
            output_file = os.path.join(output_dir, f"{subject.split('#')[-1].split('/')[-1]}.md")
            with open(output_file, 'w', encoding="utf-8") as f:
                f.write(rendered)

        # Generate an index page
        index_template = env.get_template('index_template.md')
        index_rendered = index_template.render(subjects=subjects)
        with open(os.path.join(output_dir, 'index.md'), 'w') as f:
            f.write(index_rendered)

if __name__ == "__main__":
    ontology = ""
    with open("./data/supplychain.ttl", "r", encoding='utf-8') as file:
        ontology = file.read()
    gv = GraphVisitor()
    gv.parse("./data/supplychain.ttl","text/turtle")
    renderer = GraphRenderer(gv.graph)
    renderer.render()
    print("Done")