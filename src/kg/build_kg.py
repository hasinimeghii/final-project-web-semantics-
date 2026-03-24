import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
import os

def build_kg(csv_path: str, out_nt: str, out_ttl: str):
    df = pd.read_csv(csv_path)

    g = Graph()
    EX = Namespace("http://example.org/basketball#")
    g.bind("ex", EX)

    # Classes
    Player = EX.Player
    Team = EX.Team
    Game = EX.Game
    Season = EX.Season

    # Properties
    plays_for = EX.plays_for
    played_in = EX.played_in
    scored_in = EX.scored_in
    played_against = EX.played_against
    in_season = EX.in_season

    for idx, row in df.iterrows():
        # Clean entity names (replace spaces with underscores)
        player_name = str(row['player']).replace(' ', '_')
        team_name = str(row['team']).replace(' ', '_')
        opponent_name = str(row['opponent']).replace(' ', '_')
        game_id = f"Game_{row['game_id']}"
        season_year = f"Season_{row['season']}"

        # Create URIs
        player_uri = EX[player_name]
        team_uri = EX[team_name]
        opponent_uri = EX[opponent_name]
        game_uri = EX[game_id]
        season_uri = EX[season_year]

        # Add types
        g.add((player_uri, RDF.type, Player))
        g.add((team_uri, RDF.type, Team))
        g.add((opponent_uri, RDF.type, Team))
        g.add((game_uri, RDF.type, Game))
        g.add((season_uri, RDF.type, Season))

        # Add relations
        # plays_for(Player -> Team)
        g.add((player_uri, plays_for, team_uri))
        
        # played_in(Player -> Game)
        g.add((player_uri, played_in, game_uri))

        # scored_in(Player -> Game)
        g.add((player_uri, scored_in, game_uri))

        # played_against(Game -> Team)
        g.add((game_uri, played_against, opponent_uri))

        # in_season(Game -> Season)
        g.add((game_uri, in_season, season_uri))

    # Calculate some KB statistics
    num_triples = len(g)
    print(f"Knowledge Graph built successfully with {num_triples} triples.")
    
    # Save the graphs
    os.makedirs(os.path.dirname(out_nt), exist_ok=True)
    g.serialize(destination=out_nt, format="nt")
    g.serialize(destination=out_ttl, format="turtle")
    print(f"Saved artifacts to {out_nt} and {out_ttl}")

if __name__ == "__main__":
    csv_file = "data/basketball.csv"
    out_nt = "kg_artifacts/expanded.nt"
    out_ttl = "kg_artifacts/ontology.ttl"
    build_kg(csv_file, out_nt, out_ttl)
