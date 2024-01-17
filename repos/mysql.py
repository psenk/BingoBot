from mysql.connector import connect, Error
from getpass import getpass
import os
from dotenv import load_dotenv
load_dotenv()

# connecting with mysql server


DB_LOCALHOST = os.getenv("MYSQL_LOCALHOST")
DB_USER_NAME = os.getenv("MYSQL_USER_NAME")
DB_PW = os.getenv("MYSQL_PW")

try:
    with connect(host=DB_LOCALHOST, user=DB_USER_NAME, password=DB_PW) as connection:
        
        pass
        
except Error as e:
    print(e)