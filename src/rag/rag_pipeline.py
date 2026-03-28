import rdflib
import ollama
import re

class BasketballRAG:
    def __init__(self, onto_path):
        self.g = rdflib.Graph()
        self.g.parse(onto_path, format="application/rdf+xml")
        self.schema_summary = """
        Prefix: ex: <http://example.org/basketball#>
        Classes: Player, Team, Game, Season
        Properties:
        - plays_for(Player, Team)
        - played_in(Player, Game)
        - scored_in(Player, Game)
        - played_against(Game, Team)
        - in_season(Game, Season)
        - teammate_of(Player, Player)
        - scored_against(Player, Team)
        """
        self.model = 'llama3' # ensure user has llama3 installed via ollama run llama3
        
    def generate_sparql(self, question, error_msg=None, prev_query=None):
        prompt = f"You are a SPARQL expert. Convert this question into a valid SPARQL query for our knowledge graph.\n"
        prompt += f"Schema:\n{self.schema_summary}\n\n"
        
        if error_msg:
            prompt += f"Your previous query:\n{prev_query}\nFailed with error: {error_msg}\n"
            prompt += "Please fix the SPARQL query.\n"
            
        prompt += f"Question: {question}\n\n"
        prompt += "IMPORTANT: Return ONLY the raw SPARQL query, starting with PREFIX and SELECT. Do not include markdown blocks or any other explanation."
        
        try:
            response = ollama.chat(model=self.model, messages=[{'role': 'user', 'content': prompt}])
            query = response['message']['content'].strip()
            # Clean up potential markdown formatting from LLM
            match = re.search(r'```(?:sparql)?(.*?)```', query, re.DOTALL | re.IGNORECASE)
            if match:
                query = match.group(1).strip()
            else:
                # Remove inline backticks if any
                query = query.replace('`', '').strip()
                
            if "prefix ex:" not in query.lower():
                query = "PREFIX ex: <http://example.org/basketball#>\n" + query
                
            return query
        except Exception as e:
            print(f"LLM Error: {e}")
            return None
            
    def execute_query(self, query):
        try:
            qres = self.g.query(query)
            results = []
            for row in qres:
                results.append([str(col) for col in row])
            return results, None
        except Exception as e:
            return None, str(e)
            
    def answer_question(self, question, max_retries=2):
        print(f"\nQuestion: {question}")
        query = self.generate_sparql(question)
        print(f"Generated SPARQL:\n{query}")
        
        for attempt in range(max_retries + 1):
            results, error = self.execute_query(query)
            
            if error is None and len(results) > 0:
                print(f"Success! Found {len(results)} results.")
                return results
                
            error_msg = error if error else "Query executed successfully but returned 0 results. Check logic."
            print(f"Attempt {attempt+1} failed: {error_msg}")
            
            if attempt < max_retries:
                print("Self-repairing...")
                query = self.generate_sparql(question, error_msg, query)
                print(f"Repaired SPARQL:\n{query}")
                
        print("Failed to find an answer.")
        return []

def evaluate_rag():
    rag = BasketballRAG("kg_artifacts/basketball_reasoned.owl")
    
    questions = [
        "Which players scored against the Lakers?",
        "Who is a teammate of LeBron_James?",
        "What games did Jayson_Tatum play in?",
        "Who plays for the Warriors?",
        "What seasons were played?"
    ]
    
    for q in questions:
        res = rag.answer_question(q)
        print(f"Answer: {res}\n")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        rag = BasketballRAG("kg_artifacts/basketball_reasoned.owl")
        print("Welcome to the Basketball KG QA System (Type 'exit' to quit)")
        print("Model: llama3 via Ollama")
        while True:
            try:
                q = input("\nAsk a question: ")
                if q.strip().lower() in ['exit', 'quit']:
                    break
                if not q.strip():
                    continue
                res = rag.answer_question(q)
                print(f"Answer: {res}")
            except KeyboardInterrupt:
                break
    else:
        evaluate_rag()
