import mysql.connector
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

DB_LOCALHOST = os.getenv("MYSQL_LOCALHOST")
DB_USER_NAME = os.getenv("MYSQL_USER_NAME")
DB_PW = os.getenv("MYSQL_PW")

async def connect_to_db():    
    connection = mysql.connector.connect(host=DB_LOCALHOST, user=DB_USER_NAME, password=DB_PW, database="battle_bingo", port=3306)
    print("MYSQL: Connected to bingo database.")
    return connection

async def task_complete(team: str, task: int, player: str):
    
    team = team.lower().replace(' ', '_')
    connection = await connect_to_db()
    d = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    team_board = f"{team}_board_state"
    update_task_completion_query = f"UPDATE {team_board} SET task_completion = 1, completed_by = '{player}', completed_on = '{d}' WHERE task_id = {task};"
    print("MYSQL: Sending query -> " + update_task_completion_query)
    update_completions_query = f"INSERT INTO completions (team, player, task, date) VALUES ('{team}', '{player}', {task}, '{d}');"
    print("MYSQL: Sending query -> " + update_completions_query)
    
    connection.cursor().execute(update_task_completion_query)
    connection.cursor().execute(update_completions_query)
    connection.commit()
    
    connection.close()
    return
    
async def add_submission(task: int, url: str, player: str, team: str):
    team = team.lower().replace(' ', '_')
    connection = await connect_to_db()
    d = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    add_submission_query = f"INSERT INTO submissions (task_id, img_url, player, team, date_submitted) VALUES ({task}, '{url}', '{player}', '{team}', '{d}');"
    print("MYSQL: Sending query -> " + add_submission_query)
    
    connection.cursor().execute(add_submission_query)
    connection.commit()
    
    connection.close()
    return

async def remove_submission(task: int, team: str):
    team = team.lower().replace(' ', '_')
    connection = await connect_to_db()
    
    remove_submission_query = f"DELETE FROM submissions WHERE task_id = '{task}', team = '{team}');"
    print("MYSQL: Sending query -> " + remove_submission_query)
    
    connection.cursor().execute(remove_submission_query)
    connection.commit()
    
    connection.close()
    return
    
async def increase_completions(player: str):
    pass