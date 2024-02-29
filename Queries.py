import asyncpg
import os
import datetime
from dotenv import load_dotenv
load_dotenv(override=True)

DB_HOST = os.getenv("PG_HOST")
DB_USERNAME = os.getenv("PG_USERNAME")
DB_PW = os.getenv("PG_PASSWORD")
DB_URI = os.getenv("DATABASE_URI")
TEST_DB = "postgres://postgres:root@localhost:5432/battle_bingo"
TZ_OFFSET = -6.0

tz_info = datetime.timezone(datetime.timedelta(hours=TZ_OFFSET))

# tested good
async def connect_to_db():    
    connection = await asyncpg.connect("postgres://***USERNAME***:***PASSWORD***@***FLY DATABASE***.internal:5432/bingo_bot")
    #connection = await asyncpg.connect("postgres://postgres:root@localhost:5432/battle_bingo")
    print("PG: Connected to bingo database.")
    return connection

# tested good
async def task_complete(team: str, task: int, player: str):
    
    team_snip = team.replace(' ', '_')
    team_snip = team_snip.replace('\'', '')
    team = team.replace('\'', '')

    connection = await connect_to_db()
    d = datetime.datetime.now(tz_info).strftime("%Y-%m-%d %H:%M:%S")
    
    team_board = f"{team_snip.lower()}_board_state"
    update_task_completion_query = f"UPDATE {team_board} SET task_completion = TRUE, completed_by = '{player}', completed_on = '{d}' WHERE task_id = {task};"
    print("PG: Updating Team Board State -> " + update_task_completion_query)
    update_completions_query = f"INSERT INTO completions (team, player, task, date) VALUES ('{team}', '{player}', {task}, '{d}');"
    print("PG: Updating Completions (logs) -> " + update_completions_query)
    
    await increase_completions(connection, team_snip, player)
    
    await connection.execute(update_task_completion_query)
    await connection.execute(update_completions_query)
    
    await connection.close()

# tested good
async def add_submission(task: int, img_url: str, jump_url: str, player: str, team: str, channel_id, message_id):
    connection = await connect_to_db()
    team = team.replace('\'', '')
    d = datetime.datetime.now(tz_info).strftime("%Y-%m-%d %H:%M:%S")    
    add_submission_query = f"INSERT INTO submissions (task_id, img_url, jump_url, channel_id, message_id, player, team, date_submitted) VALUES ({task}, '{img_url}', '{jump_url}', {channel_id}, {message_id}, '{player}', '{team}', '{d}');"
    print("PG: Adding Submission -> " + add_submission_query)    
    await connection.execute(add_submission_query)    
    await connection.close()

# tested good
async def remove_submission(task: int, team: str):
    connection = await connect_to_db()
    team = team.replace('\'', '')
    remove_submission_query = f"DELETE FROM submissions WHERE task_id = {task} AND team = '{team}';"
    print("PG: Removing Submission -> " + remove_submission_query)    
    await connection.execute(remove_submission_query)    
    await connection.close()

# tested good
async def remove_submission_by_id(submission_id: int):
    connection = await connect_to_db()    
    remove_submission_query = f"DELETE FROM submissions WHERE submission_id = '{submission_id}';"
    print("PG: Deleting Submission -> " + remove_submission_query)    
    await connection.execute(remove_submission_query)    
    await connection.close()
    return

# tested good
async def get_submissions():
    connection = await connect_to_db()    
    tx = connection.transaction()
    await tx.start()
    try:
        get_submissions_query = f"SELECT * FROM submissions;"
        print("PG: Getting All Submissions -> " + get_submissions_query)
        cursor = await connection.cursor(get_submissions_query)
        return_list = await cursor.fetch(100)
    except:
        await tx.rollback()
        print("EXCEPTION: get_submissions")
    else:
        await tx.commit()        
    await connection.close()
    return return_list

# tested good
async def increase_completions(connection, team: str, player: str):    
    # is player in table?
    team_list_query = f"SELECT * FROM {team} WHERE player_name = '{player}';"
    print("PG: Getting Player -> " + team_list_query)    
    tx = connection.transaction()
    await tx.start()
    try:
        cursor = await connection.cursor(team_list_query)
        team_list = await cursor.fetch(100)        
        if len(team_list) == 0:
            new_player_query = f"INSERT INTO {team} (player_name, tasks_completed) VALUES ('{player}', 1);"
            print("PG: Increasing New Player Task Completions -> " + new_player_query)
            await connection.execute(new_player_query)            
        else:
            old_value_query = f"SELECT tasks_completed FROM {team} WHERE player_name = '{player}';"
            print("PG: Getting Old Player Task Completions -> " + old_value_query)
            cursor = await connection.cursor(old_value_query)
            item = await cursor.fetch(1)
            old_value = item[0].get('tasks_completed')                
            old_player_query = f"UPDATE {team} SET tasks_completed = {old_value + 1} WHERE player_name = '{player}';"
            print("PG: Increasing Old Player Task Completions -> " + old_player_query)
            await connection.execute(old_player_query)
    except:
        await tx.rollback()
        print("EXCEPTION: increase_completions")
    else:
        await tx.commit()
    
    
async def is_task_completed(task: int):
    pass


async def update_unlocked_tasks(start: int, end: int):
    connection = await connect_to_db()
    update_unlocked_tasks_query = f"UPDATE settings SET setting_start = {start}, setting_end = {end} WHERE setting_name = 'days_unlocked'"
    print("PG: Updating Unlocked Tasks -> " + update_unlocked_tasks_query)
    await connection.execute(update_unlocked_tasks_query)
    await connection.close()
    
async def get_unlocked_tasks():
    connection = await connect_to_db()
    
    tx = connection.transaction()
    await tx.start()
    try:
        get_unlocked_tasks_query = f"SELECT * FROM settings WHERE setting_name = 'days_unlocked'"
        print("PG: Getting Unlocked Tasks -> " + get_unlocked_tasks_query)
        cursor = await connection.cursor(get_unlocked_tasks_query)
        return_list = await cursor.fetch(1)
            
        start = return_list[0].get('setting_start')
        end = return_list[0].get('setting_end')
    except:
        await tx.rollback()
        print("EXCEPTION: get_unlocked_tasks")
        return
    else:
        await tx.commit()        
    await connection.close()
    return (start, end)
