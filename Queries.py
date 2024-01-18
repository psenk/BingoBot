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
    
    team_snip = team.lower().replace(' ', '_')
    connection = await connect_to_db()
    d = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    team_board = f"{team_snip}_board_state"
    update_task_completion_query = f"UPDATE {team_board} SET task_completion = 1, completed_by = '{player}', completed_on = '{d}' WHERE task_id = {task};"
    print("MYSQL: Sending query -> " + update_task_completion_query)
    update_completions_query = f"INSERT INTO completions (team, player, task, date) VALUES ('{team}', '{player}', {task}, '{d}');"
    print("MYSQL: Sending query -> " + update_completions_query)
    
    await increase_completions(connection, team, player)
    
    connection.cursor().execute(update_task_completion_query)
    connection.cursor().execute(update_completions_query)
    connection.commit()
    
    connection.close()
    return
    
async def add_submission(task: int, url: str, player: str, team: str, channel_id, message_id):
    connection = await connect_to_db()
    d = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    add_submission_query = f"INSERT INTO submissions (task_id, img_url, channel_id, message_id, player, team, date_submitted) VALUES ({task}, '{url}', {channel_id}, {message_id}, '{player}', '{team}', '{d}');"
    print("MYSQL: Sending query -> " + add_submission_query)
    
    connection.cursor().execute(add_submission_query)
    connection.commit()
    
    connection.close()
    return

async def remove_submission(task: int, team: str):
    connection = await connect_to_db()
    
    remove_submission_query = f"DELETE FROM submissions WHERE (task_id = {task} AND team = '{team}');"
    print("MYSQL: Sending query -> " + remove_submission_query)
    
    connection.cursor().execute(remove_submission_query)
    connection.commit()
    
    connection.close()
    return

async def remove_submission(submission_id: int):
    connection = await connect_to_db()
    
    remove_submission_query = f"DELETE FROM submissions WHERE submission_id = {submission_id};"
    print("MYSQL: Sending query -> " + remove_submission_query)
    
    connection.cursor().execute(remove_submission_query)
    connection.commit()
    
    connection.close()
    return

async def get_submissions():
    connection = await connect_to_db()
    
    get_submissions_query = f"SELECT * FROM submissions;"
    print("MYSQL: Sending query -> " + get_submissions_query)
    cursor = connection.cursor()
    cursor.execute(get_submissions_query)
    return_list = cursor.fetchall()    
    connection.close()
    return return_list
    
async def increase_completions(connection, team: str, player: str):
    
    team_snip = team.lower().replace(' ', '_')
    
    # is player in table?
    team_list_query = f"SELECT * FROM {team_snip} WHERE player_name = '{player}';"  
    print("MYSQL: Sending query -> " + team_list_query)
    cursor = connection.cursor()
    cursor.execute(team_list_query)
    team_list = cursor.fetchall()
    cursor.close()
    
    if len(team_list) == 0:
        new_player_query = f"INSERT INTO {team_snip} (player_name, tasks_completed) VALUES ('{player}', 1);"
        print("MYSQL: Sending query -> " + new_player_query)
        cursor = connection.cursor()
        cursor.execute(new_player_query)
        
    else:
        old_value_query = f"SELECT tasks_completed FROM {team_snip} WHERE player_name = '{player}';"
        print("MYSQL: Sending query -> " + old_value_query)
        cursor1 = connection.cursor()
        cursor1.execute(old_value_query)
        (old_value,) = cursor1.fetchone()
        
        cursor2 = connection.cursor()        
        old_player_query = f"UPDATE {team_snip} SET tasks_completed = {int(old_value) + 1} WHERE player_name = '{player}';"
        print("MYSQL: Sending query -> " + old_player_query)
        cursor2.execute(old_player_query)
    
    connection.commit()