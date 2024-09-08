import requests
import psycopg2

class TeamManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def fetch_image_as_bytes(self, url):
        response = requests.get(url)
        return response.content

    def insert_team(self, team_id, team_name, team_logo_url):
        team_logo_bytes = self.fetch_image_as_bytes(team_logo_url)
        self.db.execute_non_query("""
            INSERT INTO Teams (team_id, team_name, team_logo)
            VALUES (%s, %s, %s)
            ON CONFLICT (team_id) DO NOTHING
        """, (team_id, team_name, psycopg2.Binary(team_logo_bytes)))
