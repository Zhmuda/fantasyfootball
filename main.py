from db_manager import DBManager
from match_manager import MatchManager
from player_manager import PlayerManager
from team_manager import TeamManager

def main():
    # Создание экземпляра DBManager
    db_manager = DBManager(dbname="fantasy_football_test", user="postgres", password="postgres")

    # Создание экземпляра MatchManager
    match_manager = MatchManager(db_manager)

    # Выполнение операций
    match_manager.check_and_fetch_yesterday_matches()
    match_manager.find_matches()

    # Закрытие соединения с базой данных
    db_manager.close()

    # Список интересующих лиг  RPL-235 AZP-419   | RPL pages 28 | AZP pages 13 | (+1)
    league_id = "235"
    season = '2024'
    pages = 14

if __name__ == "__main__":
    main()
