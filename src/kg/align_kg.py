import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
import os

def generate_alignments(csv_path: str, out_ttl: str):
    df = pd.read_csv(csv_path)

    g = Graph()
    EX = Namespace("http://example.org/basketball#")
    DBP = Namespace("http://dbpedia.org/resource/")
    OWL = Namespace("http://www.w3.org/2002/07/owl#")
    
    g.bind("ex", EX)
    g.bind("dbp", DBP)
    g.bind("owl", OWL)

    # Predicate alignment
    g.add((EX.plays_for, OWL.equivalentProperty, DBP.memberOf))

    # Entity linking (mock DBpedia matching)
    for idx, row in df.iterrows():
        player_name_raw = str(row['player'])
        team_name_raw = str(row['team'])

        # Create URIs
        player_uri = EX[player_name_raw.replace(' ', '_')]
        team_uri = EX[team_name_raw.replace(' ', '_')]
        
        # Simple string-matching alignment logic
        dbp_player_uri = DBP[player_name_raw.replace(' ', '_')]
        dbp_team_uri = DBP[team_name_raw.replace(' ', '_') + "_(basketball)"]

        # Add sameAs
        g.add((player_uri, OWL.sameAs, dbp_player_uri))
        g.add((team_uri, OWL.sameAs, dbp_team_uri))

    os.makedirs(os.path.dirname(out_ttl), exist_ok=True)
    g.serialize(destination=out_ttl, format="turtle")
    print(f"Alignment graph with {len(g)} triples saved to {out_ttl}")

if __name__ == "__main__":
    csv_file = "data/basketball.csv"
    out_ttl = "kg_artifacts/alignment.ttl"
    generate_alignments(csv_file, out_ttl)
