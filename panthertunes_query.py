import sqlite3
import random
import datetime
import hashlib
import time
import string

# add a user to database
def add_user(new_username, new_password, email):
    conn = sqlite3.connect("Databases/users.db")#check if the username and email are unique (this is purely for user feedback)
    cur = conn.cursor()                         #as emails and usernames being unique is also enforced by the db

    sql = f'''
        SELECT username, email FROM UsersTable
        WHERE username = '{new_username}' OR email = '{email}'
    '''

    cur.execute(sql)
    result = cur.fetchall()
    for i in range(len(result)):
        if result[i][1] == email:
            return 'email not unique'
        if result[i][0] == new_username:
            return 'username not unique'
    
    #create random ids and necessary info
    rand_user_id = random.randrange(0, 9000000)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hashed_pw = hash_hex(new_password)

    sql = '''
    INSERT INTO UsersTable(user_id, username, pw, 
        joined, last_accessed, num_accessed, email, posts, projects)
    VALUES(?,?,?,?,?,?,?,?,?)
    '''

    try:
        cur.execute(sql, (rand_user_id, new_username, hashed_pw, now, now, 0, email, '', ''))
        conn.commit()
    
    except sqlite3.IntegrityError:
        # if by coincidence, we try to add another user id that already exists, try again
        cur.close()
        conn.close()  
        add_user(new_username, new_password, email)

    cur.close()
    conn.close()

    return 'done'

def add_post(post_id, project_id, username, timestamp, title, post, music_genre, help_needed, likes=0):
    conn = sqlite3.connect("Databases/posts.db")
    cur = conn.cursor()

    sql = f'''
    INSERT INTO PostsTable(post_id, project_id, username, timestamp,
        title, post, music_genre, help_needed, likes)
    VALUES(?,?,?,?,?,?,?,?,?)
    '''

    try:
        cur.execute(sql, (post_id, project_id, username, timestamp, title, post, music_genre, help_needed, likes))
        conn.commit()
    except:
        print('error')
    
    cur.close()
    conn.close()

    return 'done'

def add_project(project_id, username, title, desc, post_id, chat_id):
    conn = sqlite3.connect("Databases/projects.db")
    cur = conn.cursor()

    sql = f'''
    INSERT INTO ProjectsTable(project_id, usernames, title,
        desc, post_ids, chat_id)
    VALUES(?,?,?,?,?,?)
    '''

    try:
        cur.execute(sql, (project_id, username, title, desc, str(post_id) + ' ', chat_id))
        conn.commit()
    except:
        print('error')
    
    cur.close()
    conn.close()

    return 'done'

def get_all_posts(user_id=''):
    conn = sqlite3.connect("Databases/posts.db")
    cur = conn.cursor()

    post_ids = ''
    if user_id != '':
        conn2 = sqlite3.connect("Databases/users.db")
        cur2 = conn2.cursor()
        
        sql2 = f'''
        SELECT posts FROM UsersTable
        WHERE user_id='{user_id}'
        '''
        cur2.execute(sql2)
        result = cur2.fetchall()
        post_ids = result[0][0]
        cur2.close()
        conn2.close()
        if not post_ids or post_ids == '':
            return []
    if post_ids == '':
        sql = '''SELECT * from PostsTable ORDER by timestamp'''
        try:
            cur.execute(sql)
            records = cur.fetchall()
            cur.close()
            conn.close()
            return records
        except sqlite3.Error as error:
            print("Failed to read data from sqlite table", error)
    else:
        post_idSequence = post_ids.split(' ')
        if len(post_idSequence) > 0 and post_idSequence[len(post_idSequence) - 1] == '':
            post_idSequence.pop()
        records = []
        for post_id in post_idSequence:
            sql = f'''
            SELECT * FROM PostsTable
            WHERE post_id='{post_id}'
            '''
            try:
                cur.execute(sql)
                record = cur.fetchall()
                records.append(record[0])
            except sqlite3.Error as error:
                print("Failed to read data from sqlite table", error)
        cur.close()
        conn.close()
        return records

def get_all_projects(user_id):
    conn = sqlite3.connect("Databases/projects.db")
    cur = conn.cursor()
    conn2 = sqlite3.connect("Databases/users.db")
    cur2 = conn2.cursor()
    
    project_ids = ''
    
    sql2 = f'''
    SELECT projects FROM UsersTable
    WHERE user_id='{user_id}'
    '''

    cur2.execute(sql2)
    result = cur2.fetchall()
    project_ids = result[0][0]
    cur2.close()
    conn2.close()
    if not project_ids or project_ids == '':
        return []
    project_idSequence = project_ids.split(' ')
    if len(project_idSequence) > 0 and project_idSequence[len(project_idSequence) - 1] == '':
        project_idSequence.pop()
    records = []
    for project_id in project_idSequence:
        sql = f'''
        SELECT * FROM ProjectsTable
        WHERE project_id='{project_id}'
        '''
        try:
            cur.execute(sql)
            record = cur.fetchall()
            records.append(record[0])
        except sqlite3.Error as error:
            print("Failed to read data from sqlite table", error)
    cur.close()
    conn.close()
    return records

#checks if user_id exists in table
def check_valid_id(user_id):
    user_id = int(user_id)
    
    conn = sqlite3.connect("Databases/users.db")
    cur = conn.cursor()

    sql= f'''
    SELECT EXISTS(
        SELECT * FROM UsersTable 
        WHERE user_id='{user_id}'
        );
    '''

    cur.execute(sql)
    result = cur.fetchall()
    cur.close()
    conn.close()

    #exists contains 0 or 1
    exists = result[0][0]

    #convert 1 to True and 0 to False
    if exists == 1:
        exists = True
    else:
        exists = False     

    return exists

#checks if username exists in table
def check_valid_username(username):
    #sql in
    conn = sqlite3.connect("Databases/users.db")
    cur = conn.cursor()

    sql= f'''
    SELECT EXISTS(
        SELECT * FROM UsersTable 
        WHERE username='{username}'
        );
    '''

    cur.execute(sql)
    result = cur.fetchall()
    cur.close()
    conn.close()

    #exists contains 0 or 1
    exists = result[0][0]

    #convert 1 to True and 0 to False
    if exists == 1:
        exists = True
    else:
        exists = False     

    return exists    

def hash_hex(password):
    encoded = password.encode()
    result = hashlib.sha256(encoded)
    return result.hexdigest()

# username must exist, so check if username exists before using this function
def check_for_password(username, password):
    hashed_pw = hash_hex(password)
    #sql in

    conn = sqlite3.connect("Databases/users.db")
    cur = conn.cursor()

    sql= f'''
    SELECT EXISTS(
        SELECT * FROM UsersTable 
        WHERE username='{username}' AND pw='{hashed_pw}'
        );
    '''

    cur.execute(sql)
    result = cur.fetchall()
    cur.close()
    conn.close()

    #exists contains 0 or 1
    exists = result[0][0]

    #convert 1 to True and 0 to False
    if exists == 1:
        exists = True
    else:
        exists = False     

    return exists


def get_user_id(username):
    #sql in
    conn = sqlite3.connect("Databases/users.db")
    cur = conn.cursor()

    sql = f'''
    SELECT user_id FROM UsersTable
    WHERE username='{username}'
    '''

    cur.execute(sql)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()

    user_id = result[0][0]

    return user_id  

def get_username(userid):
    conn = sqlite3.connect("Databases/users.db")
    cur = conn.cursor()

    sql = f'''
    SELECT username FROM UsersTable
    WHERE user_id='{userid}'
    '''

    cur.execute(sql)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()

    username = result[0][0]

    return username

def insert_token_table(user_id, hashed_token):
    conn = sqlite3.connect("Databases/tokens.db")
    cur = conn.cursor()

    now = int(time.time())#datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sql = '''
    INSERT INTO TokensTable (FK_user_id, user_token_hashed, last_used_date)
    VALUES (?,?,?)
    '''

    try:
        cur.execute(sql, (user_id, hashed_token, now))
        conn.commit()
    except Exception as e:
        #print(e)
        return False    

    cur.close()
    conn.close()

    return True


def delete_by_token(hashed_token):
    try:
        #sql in
        conn = sqlite3.connect("Databases/tokens.db")
        cur = conn.cursor()

        sql = f'''
        DELETE FROM TokenTable
        WHERE user_token_hashed = '{hashed_token}'
        '''

        cur.execute(sql)
        conn.commit()

        cur.close()
        conn.close()
        return True
    except:
        return False

def delete_all_tokens(user_id):
    conn = sqlite3.connect("Databases/tokens.db")
    cur = conn.cursor()

    sql = f'''
    DELETE FROM TokenTable
    WHERE FK_user_id = '{user_id}'
    '''

    cur.execute(sql)
    conn.commit()

    cur.close()
    conn.close()

def token_to_user_id(token):
    hashed_token = hash_hex(token)

    conn = sqlite3.connect("Databases/tokens.db")
    cur = conn.cursor()

    sql = f'''
    SELECT FK_user_id FROM TokenTable
    WHERE user_token_hashed='{hashed_token}'
    '''

    cur.execute(sql)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()

    user_id = result[0][0]

    #we have just used the token so lets update the last used!
    conn = sqlite3.connect("Databases/tokens.db")
    cur = conn.cursor()

    now = int(time.time())#datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = f'''
    UPDATE TokenTable
    SET last_used_date = '{now}'
    WHERE user_token_hashed = '{hashed_token}'
    '''

    cur.execute(sql)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    
    return user_id

def create_token_and_table(user_id):
    #create random token
    rand_token = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(32))

    #hash and put in TokenTable
    hashed_token = hash_hex(rand_token)
    success = insert_token_table(user_id, hashed_token)

    # if we find duplicate token (which is rare in itself) then we just try again (we would actually be cursed if we generate
    # three duplicate random tokens in a row lol)
    if not success:
        rand_token = create_token_and_table(user_id)

    return rand_token

def update_last_accessed_date(new_date, user_id):
    conn = sqlite3.connect("Databases/users.db")
    cur = conn.cursor()

    sql = f'''
    UPDATE UsersTable
    SET last_accessed='{new_date}'
    WHERE user_id = '{user_id}';
    '''
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close() 

def update_num_accessed(user_id):
    conn = sqlite3.connect("Databases/users.db")
    cur = conn.cursor()

    sql = f'''
    UPDATE UsersTable
    SET num_accessed=num_accessed+1
    WHERE user_id = '{user_id}';
    '''

    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

def update_posts_from_user(user_id, post_id):
    conn = sqlite3.connect("Databases/users.db")
    cur = conn.cursor()

    post_idStr = str(post_id) + ' '
    sql = f'''
    UPDATE UsersTable
    SET posts=posts || '{post_idStr}'
    WHERE user_id='{user_id}';
    '''

    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

def update_projects_from_user(user_id, project_id):
    conn = sqlite3.connect("Databases/users.db")
    cur = conn.cursor()

    project_idStr = str(project_id) + ' '
    sql = f'''
    UPDATE UsersTable
    SET projects=projects || '{project_idStr}'
    WHERE user_id='{user_id}';
    '''

    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

def update_posts_from_project(project_id, post_id):
    conn = sqlite3.connect("Databases/projects.db")
    cur = conn.cursor()

    post_idStr = str(post_id) + ' '
    print(post_idStr)
    sql = f'''
    UPDATE ProjectsTable
    SET post_ids=post_ids || '{post_idStr}'
    WHERE project_id='{project_id}';
    '''
    try:
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
    except:
        print('update_posts_from_project error')

def delete_post(post_id):
    # delete from posts.db
    conn = sqlite3.connect("Databases/posts.db")
    cur = conn.cursor()
    project_id = 0
    user_id = ''

    try:
        sql = f'''
        SELECT project_id, username FROM PostsTable
        WHERE post_id = '{post_id}'
        '''
        print(sql)
        cur.execute(sql)
        result = cur.fetchall()
        print(result)
        project_id = result[0][0]
        username = result[0][1]
        user_id = get_user_id(username)
        sql = f'''
        DELETE FROM PostsTable
        WHERE post_id = '{post_id}'
        '''
        print("post_id =", post_id)
        cur.execute(sql)
        conn.commit()
    except Exception as e:
        print('error in deleting from posts.db', e)

    cur.close()
    conn.close()
    
    conn2 = sqlite3.connect("Databases/users.db")
    cur2 = conn2.cursor()

    try:
        sql2 = f'''
        SELECT posts FROM UsersTable
        WHERE user_id='{user_id}'
        '''
        cur2.execute(sql2)
        result2 = cur2.fetchall()
        posts = result2[0][0]
        post_replacement = posts.replace(str(post_id) + ' ', '')
        sql2 = f'''
        UPDATE UsersTable
        SET posts='{post_replacement}'
        WHERE user_id='{user_id}';
        '''
        print("user_id =", user_id, "and post_replacement =", post_replacement)
        cur2.execute(sql2)
        conn2.commit()
    except Exception as e:
        print('error in updating users.db', e)

    cur2.close()
    conn2.close()

    if project_id == 0:
        return 'done'
    
    conn3 = sqlite3.connect("Databases/projects.db")
    cur3 = conn3.cursor()

    try:
        sql3 = f'''
        SELECT post_ids FROM ProjectsTable
        WHERE project_id='{project_id}'
        '''
        cur3.execute(sql3)
        result3 = cur3.fetchall()
        post_ids = result3[0][0]
        post_idsReplacement = post_ids.replace(str(post_id) + ' ', '')
        sql3 = f'''
        UPDATE ProjectsTable
        SET post_ids='{post_idsReplacement}'
        WHERE project_id='{project_id}';
        '''
        print("project_id =", project_id, "and post_idsReplacement =", post_idsReplacement)
        cur3.execute(sql3)
        conn3.commit()
    except Exception as e:
        print('error in updating projects.db', e)
    
    cur3.close()
    conn3.close()

    return 'done'