from owlready2 import *
import pandas as pd
import os

def build_and_reason(csv_path: str, out_owl: str):
    onto_path.append("kg_artifacts")
    onto = get_ontology("http://example.org/basketball.owl")

    with onto:
        # Define Classes
        class Player(Thing): pass
        class Team(Thing): pass
        class Game(Thing): pass
        class Season(Thing): pass

        # Define Properties
        class plays_for(ObjectProperty):
            domain = [Player]
            range = [Team]

        class played_in(ObjectProperty):
            domain = [Player]
            range = [Game]

        class scored_in(ObjectProperty):
            domain = [Player]
            range = [Game]

        class played_against(ObjectProperty):
            domain = [Game]
            range = [Team]

        class in_season(ObjectProperty):
            domain = [Game]
            range = [Season]

        # Inferred Properties
        class teammate_of(ObjectProperty):
            domain = [Player]
            range = [Player]

        class scored_against(ObjectProperty):
            domain = [Player]
            range = [Team]

    # Load Data
    df = pd.read_csv(csv_path)

    # Dictionary to keep track of instances to avoid duplicates
    instances = {}

    def get_instance(cls, name):
        name_clean = str(name).replace(' ', '_').replace("'", "")
        if name_clean not in instances:
            instances[name_clean] = cls(name_clean)
        return instances[name_clean]

    for idx, row in df.iterrows():
        p = get_instance(Player, row['player'])
        t = get_instance(Team, row['team'])
        opp = get_instance(Team, row['opponent'])
        g = get_instance(Game, f"Game_{row['game_id']}")
        s = get_instance(Season, f"Season_{row['season']}")

        # Assign relationships
        if t not in p.plays_for: p.plays_for.append(t)
        if g not in p.played_in: p.played_in.append(g)
        if g not in p.scored_in: p.scored_in.append(g)
        if opp not in g.played_against: g.played_against.append(opp)
        if s not in g.in_season: g.in_season.append(s)

    # SWRL Rules
    with onto:
        # Rule 1: Teammates (if x plays for t and y plays for t, and x != y -> x teammate_of y)
        rule1 = Imp()
        rule1.set_as_rule("""Player(?x), Team(?t), plays_for(?x, ?t), Player(?y), plays_for(?y, ?t), DifferentFrom(?x, ?y) -> teammate_of(?x, ?y)""")

        # Rule 2: Scored Against (if x scored in g and g played against t -> x scored against t)
        rule2 = Imp()
        rule2.set_as_rule("""Player(?x), Game(?g), Team(?t), scored_in(?x, ?g), played_against(?g, ?t) -> scored_against(?x, ?t)""")

    print("Running Pellet reasoner to infer new relationships...")
    sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True)
    
    # Save ontology with inferences
    os.makedirs(os.path.dirname(out_owl), exist_ok=True)
    onto.save(file=out_owl, format="rdfxml")
    print(f"Ontology with reasoned inferences saved to {out_owl}")

if __name__ == "__main__":
    csv_file = "data/basketball.csv"
    out_owl = "kg_artifacts/basketball_reasoned.owl"
    build_and_reason(csv_file, out_owl)
