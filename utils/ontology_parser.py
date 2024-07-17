from rdflib import Graph, RDF, RDFS, OWL, URIRef
import os
import sqlite3
import rdflib
from rdflib.namespace import RDF, RDFS, OWL, XSD

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
                'graph_uri': s,
                'prefix': s.split('#')[-1].split('/')[-1],
                'subClasses': list(self.graph.objects(s, RDFS.subClassOf)),
                'superClasses': list(self.graph.subjects(RDFS.subClassOf, s)),
                'annotations': {p: list(self.graph.objects(s, p)) for p in self.graph.predicates(s, None)},
                'properties': {p: list(self.graph.objects(s, p)) for p in self.graph.predicates(s, RDF.Property)},
                'type': list(self.graph.objects(s, RDF.type)),
                'relations': list(self.graph.objects(s, None)),
                URIRef :URIRef
            }

        # Create output directory
        output_dir = '.cache/docs/ontology'
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
            # suppress all \n that occure more than 2 times
            rendered = '\n'.join([line for line in rendered.split('\n') if line.strip() or line.strip() == '\n'])

            # Save the rendered Markdown to a file
            output_file = os.path.join(output_dir, f"{subject.split('#')[-1].split('/')[-1]}.md")
            with open(output_file, 'w', encoding="utf-8") as f:
                f.write(rendered)

            # if it is a class, create a model template
            # if RDFS.Class in details['annotations'].get(RDF.type, []):
            #     template = env.get_template('model_template.py')
            #     rendered = template.render(
            #         subject=subject,
            #         subClasses=details['subClasses'],
            #         superClasses=details['superClasses'],
            #         annotations=details['annotations'],
            #         properties=details['properties']
            #     )
            #     # Save the rendered Markdown to a file
            #     output_file = os.path.join(output_dir, f"{subject.split('#')[-1].split('/')[-1]}.py")
            #     with open(output_file, 'w', encoding="utf-8") as f:
            #         f.write(rendered)
            

        # Generate an index page
        index_template = env.get_template('index_template.md')
        index_rendered = index_template.render(subjects=subjects)
        with open(os.path.join(output_dir, 'index.md'), 'w') as f:
            f.write(index_rendered)


class DatabaseOntologyWriter():
    def __init__(self) -> None:
        pass
            
    def write_ontology(self, db_path, ontology_path, namespace):

        # Define your namespaces
        xmlns = rdflib.Namespace(namespace)

        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create an RDF graph
        g = rdflib.Graph()

        # Bind the namespace
        g.bind("ai", xmlns)

        # Get all tables
        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        cursor.execute(tables_query)
        tables = cursor.fetchall()

        for table_name in tables:
            table_name = table_name[0]
            table_uri = rdflib.URIRef(namespace + table_name)
            
            # Add table to the graph
            g.add((table_uri, RDF.type, AI.DatabaseTable))
            g.add((table_uri, RDFS.label, rdflib.Literal(table_name)))
            
            # Get all columns for this table
            columns_query = f"PRAGMA table_info({table_name});"
            cursor.execute(columns_query)
            columns = cursor.fetchall()
            
            for column in columns:
                column_name = column[1]
                column_type = column[2]
                column_uri = rdflib.URIRef(namespace + table_name + "_" + column_name)
                
                # Add column to the graph
                g.add((column_uri, RDF.type, xmlns.DatabaseColumn))
                g.add((column_uri, RDFS.label, rdflib.Literal(column_name)))
                g.add((column_uri, xmlns.hasType, rdflib.Literal(column_type)))
                
                # Link column to table
                g.add((table_uri, xmlns.hasColumn, column_uri))
            
            # Get all primary keys for this table
            primary_key_query = f"PRAGMA table_info({table_name});"
            cursor.execute(primary_key_query)
            primary_keys = [col[1] for col in cursor.fetchall() if col[5]]  # col[5] is the primary key flag
            
            if primary_keys:
                primary_key_uri = rdflib.URIRef(namespace + table_name + "_PrimaryKey")
                g.add((primary_key_uri, RDF.type, xmlns.PrimaryKey))
                g.add((table_uri, xmlns.hasPrimaryKey, primary_key_uri))
                
                for pk in primary_keys:
                    pk_column_uri = rdflib.URIRef(namespace + table_name + "_" + pk)
                    g.add((primary_key_uri, xmlns.hasColumn, pk_column_uri))
            
            # Get all foreign keys for this table
            foreign_key_query = f"PRAGMA foreign_key_list({table_name});"
            cursor.execute(foreign_key_query)
            foreign_keys = cursor.fetchall()
            
            for fk in foreign_keys:
                fk_table = fk[2]
                fk_from = fk[3]
                fk_to = fk[4]
                
                foreign_key_uri = rdflib.URIRef(namespace + table_name + "_" + fk_from + "_ForeignKey")
                g.add((foreign_key_uri, RDF.type, xmlns.ForeignKey))
                
                fk_from_uri = rdflib.URIRef(namespace + table_name + "_" + fk_from)
                fk_to_uri = rdflib.URIRef(namespace + fk_table + "_" + fk_to)
                
                g.add((foreign_key_uri, xmlns.hasColumn, fk_from_uri))
                g.add((table_uri, xmlns.hasForeignKey, foreign_key_uri))
                g.add((foreign_key_uri, xmlns.connectsTo, fk_to_uri))

        # Save the graph to a file
        g.serialize(f"{ontology_path}.ttl", format="turtle")

        # Close the database connection
        conn.close()


if __name__ == "__main__":

    # db_writer = DatabaseOntologyWriter()
    # db_writer.write_ontology("data/companies.db", "./data/companiesdb.ttl", "http://chainwise.ai/app/")

    gv = GraphVisitor()
    #gv.parse("./data/supplychain.ttl","text/turtle")
    gv.parse("./ontologies/SupplyChain.rdf","xml")
   # gv.parse("./ontologies/Iof.AnnotationVocabulary.rdf","xml")
    #v.parse("./ontologies/Corporations.rdf","xml")
    #gv.parse("./ontologies/ai.ttl","text/turtle")
    #gv.parse("./ontologies/db.ttl","text/turtle")
    #gv.parse("./ontologies/docs.ttl","text/turtle")
   # gv.parse("./ontologies/app.ttl","text/turtle")
    renderer = GraphRenderer(gv.graph)
    renderer.render()
    print("Done")