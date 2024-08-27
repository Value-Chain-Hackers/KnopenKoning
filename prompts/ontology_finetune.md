## Instructions:

Given the provided part ontology part above please generate a set of triplets of (instruction, input, output) to create a fine-tuning dataset about the given ontology.
Make sure to refer to the name of the ontology as the `{ontology_name}` ontology.
The full uri of the ontology is `<{ontology_uri}>`.

**Expected Ouput**:

Make sure your output is valid JSON in a ```json``` code block.
DO ONLY output a JSON array of dictionaries each, dict should have a (instruction, input, output) key/value pair.
DO ONLY output the (instruction, input, output) pairs dicts in an array, all are required and cannot be an empty string. 
DO NOT add any additional content.
DO ONLY output valid json object, respecting quoting and escaping of special chars. 
DO ensure very diversified (instruction, input, output) set of inputs and output covering all aspects of the `{ontology_class}` in the `{ontology_name}` ontology. 
DO include questions that ask for an examples and produce a valid example in a turtle code block in the answer.
DD generate at least `{max_examples}` input, output pairs. When the answer contains rdf or turtle code, make sure to wrap it in a ``` code block.
DO make instructions and examples that are clear and easy to understand.
Do NOT make questions that only ask for a definition of a term.
If first-order logic is provided make 5 additional (instruction, input, output) that are explanatory of the provided axioms.
DO NOT explain the principles of first-order logic, only the axioms provided.
Explain the first-order logic axioms in a way that is easy to understand.
DO make questions that foster reasoning about the ontology.
DO NOT create general questions about the ontology or supply chain mapping concepts, make sure to direct the questions to the tasks of knowledge graph creation and ontology mapping given the `{ontology_class}`  class, its subclasses, relationships, etc.
DO direct the questions to the tasks of knowledge extraction, entity recognition, graph creation and ontology mapping.
Instructions should be like : 'You are a helpful AI assistant, that helps users with the `{ontology_name}` ontology. Please provide a concise but complete and clear answer to the users input question. (This is an example make sure you variate the instructions prompt too)
DO NOT add the input to the instrurctions make sure the question is in the input.
Make sure to include a variety of instructions and examples, using synonmis and different ways of asking for the same thing.
DO ONLY OUTPUT THE JSON ARRAY OF DICTIONARIES. MAKE SURE TO ESCAPE SPECIAL CHARACTERS IN THE JSON OUTPUT.

## Input:

{ontology}