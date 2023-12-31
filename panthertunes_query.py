import sqlite3
from io import BytesIO
import os
import random
import datetime
import hashlib
import time
import string
from validate_email import validate_email

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
    if not validate_email(email_address=email):
        return 'Invalid email address.'
    #create random ids and necessary info
    rand_user_id = random.randrange(0, 9000000)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hashed_pw = hash_hex(new_password)

    sql = '''
    INSERT INTO UsersTable(user_id, username, pw, 
        joined, last_accessed, num_accessed, email, posts, projects, comments_liked)
    VALUES(?,?,?,?,?,?,?,?,?,?)
    '''

    try:
        cur.execute(sql, (rand_user_id, new_username, hashed_pw, now, now, 0, email, '', '', ''))
        conn.commit()
    
    except sqlite3.IntegrityError:
        # if by coincidence, we try to add another user id that already exists, try again
        cur.close()
        conn.close()  
        add_user(new_username, new_password, email)

    cur.close()
    conn.close()

    add_table('notifications', rand_user_id)

    return 'done'

def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData

def add_post(post_id, project_id, username, timestamp, title, post, music_genre, help_needed, img=0, audio=0, video=0, likes=0, comments=0):
    conn = sqlite3.connect("Databases/posts.db")
    cur = conn.cursor()

    sql = f'''
    INSERT INTO PostsTable(post_id, project_id, username, timestamp,
        title, post, music_genre, help_needed, likes, comments, img, audio, video)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
    '''

    try:
        cur.execute(sql, (post_id, project_id, username, timestamp, title, post, music_genre.lower(), help_needed.lower(), likes, comments, img, audio, video))
        conn.commit()
    except:
        print('error')
    
    cur.close()
    conn.close()

    add_table('forums', post_id)

    return 'done'

def add_project(project_id, username, title, desc, post_id, chat_id):
    conn = sqlite3.connect("Databases/projects.db")
    cur = conn.cursor()

    sql = f'''
    INSERT INTO ProjectsTable(project_id, usernames, title,
        desc, post_ids, chat_id, requested)
    VALUES(?,?,?,?,?,?,?)
    '''

    try:
        cur.execute(sql, (project_id, username, title, desc, str(post_id) + ' ', chat_id, ''))
        conn.commit()
    except:
        print('error')
    
    cur.close()
    conn.close()

    add_table('chat', project_id)
    add_table('updates', project_id)

    return 'done'

def add_table(db, id):
    conn = sqlite3.connect("Databases/" + db + ".db")
    cur = conn.cursor()

    if db == 'forums':
        table_name = 'F' + str(id)
        sql = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            comment_id INTEGER PRIMARY KEY,
            username TEXT,
            comment TEXT,
            reply_id INTEGER,
            timestamp DATETIME,
            likes INTEGER,
            position INTEGER
        );
        '''
    elif db == 'notifications':
        table_name = 'U' + str(id)
        sql = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            notification_id INTEGER PRIMARY KEY,
            type TEXT,
            source TEXT,
            message TEXT,
            link TEXT,
            timestamp DATETIME,
            unread INTEGER DEFAULT 1
        );
        '''
    elif db == 'chat':
        table_name = 'P' + str(id)
        sql = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            username TEXT,
            msg TEXT,
            timestamp DATETIME
        );
        '''
    elif db == 'updates':
        table_name = 'P' + str(id)
        sql = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            username TEXT,
            msg TEXT,
            timestamp DATETIME
        )
        '''

    cur.execute(sql)
    conn.commit()

    return 'done'

def add_comment(comment_id, username, comment, post_id, reply_id, timestamp, likes=0, position=0):
    conn = sqlite3.connect("Databases/forums.db")
    cur = conn.cursor()
    conn2 = sqlite3.connect("Databases/posts.db")
    cur2 = conn2.cursor()

    table_name = 'F' + str(post_id)
    user_id = 0

    try:
        if reply_id != 0 and reply_id != '0':
            sql = f'''
            SELECT username, position FROM {table_name}
            WHERE comment_id='{reply_id}'
            '''

            cur.execute(sql)
            result = cur.fetchall()
            user_id = get_user_id(result[0][0])
            position = result[0][1] + 1
        else:
            sql2 = f'''
            SELECT username FROM PostsTable
            WHERE post_id='{post_id}'
            '''
            cur2.execute(sql2)
            result = cur2.fetchall()
            user_id = get_user_id(result[0][0])
        
        sql = f'''
        INSERT INTO {table_name}(comment_id, username, comment,
            reply_id, timestamp, likes, position)
        VALUES(?,?,?,?,?,?,?)
        '''

        cur.execute(sql, (comment_id, username, comment, reply_id, timestamp, likes, position))
        conn.commit()

        sql2 = f'''
        UPDATE PostsTable
        SET comments=comments+1
        WHERE post_id = '{post_id}';
        '''

        cur2.execute(sql2)
        conn2.commit()

        if user_id != get_user_id(username):
            message = username + ' replied to you: "' + comment + '"'
            add_notification(user_id, 'reply', username, message, 'post/' + str(post_id))
    except Exception as e:
        print(e.with_traceback)

    cur.close()
    conn.close()
    cur2.close()
    conn2.close()

    return 'done'

def add_application(application_id, project_id, username, pitch, timestamp):
    conn = sqlite3.connect("Databases/applications.db")
    cur = conn.cursor()
    conn2 = sqlite3.connect("Databases/projects.db")
    cur2 = conn2.cursor()

    sql = f'''
    INSERT INTO ApplicationsTable(application_id, project_id, username,
        pitch, timestamp)
    VALUES(?,?,?,?,?)
    '''

    try:
        cur.execute(sql, (application_id, project_id, username, pitch, timestamp))
        conn.commit()
    except:
        print('error')

    sql2 = f'''
    SELECT usernames, title FROM ProjectsTable
    WHERE project_id='{project_id}'
    '''

    cur2.execute(sql2)
    result = cur2.fetchall()
    usernames = result[0][0].split(' ')
    for name in usernames:
        if name == '':
            continue
        user_id = get_user_id(name)
        message = username + ' has applied to ' + result[0][1] + ': "' + pitch + '"'
        add_notification(user_id, 'apply', username, message, 'project/applications/' + str(project_id))
    
    cur.close()
    conn.close()

    return 'done'

def add_notification(user_id, type, source, message, link, unread=1):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    notification_id = random.randint(1000000, 9999999)
    conn = sqlite3.connect("Databases/notifications.db")
    cur = conn.cursor()

    table_name = 'U' + str(user_id)
    sql = f'''
    INSERT INTO {table_name}(notification_id, type, source, message,
        link, timestamp, unread)
    VALUES(?,?,?,?,?,?,?)
    '''

    try:
        cur.execute(sql, (notification_id, type, source, message, link, timestamp, unread))
        conn.commit()
    except:
        print('notification error')
    
    cur.close()
    conn.close()

    return 'done'

def add_contest(contest_id, user_id, project_id, desc, timestamp):
    conn = sqlite3.connect("Databases/contests.db")
    cur = conn.cursor()

    sql = f'''
    INSERT INTO ContestsTable(contest_id, user_id, project_id,
        desc, timestamp)
    VALUES(?,?,?,?,?)
    '''

    try:
        cur.execute(sql, (contest_id, user_id, project_id, desc, timestamp))
        conn.commit()
    except:
        print('notification error')
    
    cur.close()
    conn.close()

    return 'done'

def add_chat(project_id, username, msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("Databases/chat.db")
    cur = conn.cursor()
    conn2 = sqlite3.connect("Databases/projects.db")
    cur2 = conn2.cursor()

    table_name = 'P' + str(project_id)
    sql = f'''
    INSERT INTO {table_name}(username, msg, timestamp)
    VALUES(?,?,?)
    '''

    try:
        cur.execute(sql, (username, msg, timestamp))
        conn.commit()
    except:
        print('chat error')

    sql2 = f'''
    SELECT usernames, active FROM ProjectsTable
    WHERE project_id='{project_id}'
    '''

    cur2.execute(sql2)
    records = cur2.fetchall()
    username_list = records[0][0].split(' ')
    for user in username_list:
        if (user not in records[0][1]):
            add_notification(get_user_id(user), 'chat', project_id, '', '', unread=0)
    
    cur.close()
    conn.close()

    return 'done'

def add_update_to_project(project_id, username, msg, timestamp):
    conn = sqlite3.connect("Databases/updates.db")
    cur = conn.cursor()

    table_name = 'P' + str(project_id)
    sql = f'''
    INSERT INTO {table_name}(username, msg, timestamp)
    VALUES(?,?,?)
    '''

    try:
        cur.execute(sql, (username, msg, timestamp))
        conn.commit()
    except:
        print('update error')
    
    cur.close()
    conn.close()

    return 'done'

def read_all_notifications(user_id):
    conn = sqlite3.connect("Databases/notifications.db")
    cur = conn.cursor()

    table_name = 'U' + str(user_id)
    sql = f'''
    UPDATE {table_name}
    SET unread=0
    WHERE unread = 1;
    '''

    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

    return 'done'

def get_unread_number(user_id):
    conn = sqlite3.connect("Databases/notifications.db")
    cur = conn.cursor()

    table_name = 'U' + str(user_id)
    sql = f'''
    SELECT * FROM {table_name}
    WHERE unread = 1
    '''

    cur.execute(sql)
    records = cur.fetchall()
    unread_number = len(records)
    cur.close()
    conn.close()

    return unread_number

def get_unread_chats_from_project(project_id, user_id):
    conn = sqlite3.connect("Databases/notifications.db")
    cur = conn.cursor()

    table_name = 'U' + str(user_id)
    sql = f'''
    SELECT notification_id FROM {table_name}
    WHERE type='chat' AND source='{project_id}'
    '''

    cur.execute(sql)
    records = cur.fetchall()
    cur.close()
    conn.close()
    
    return len(records)

def read_all_chats(project_id, user_id):
    conn = sqlite3.connect("Databases/notifications.db")
    cur = conn.cursor()

    table_name = 'U' + str(user_id)
    sql = f'''
    DELETE FROM {table_name}
    WHERE type='chat' AND source='{project_id}'
    '''

    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

    return 'done'

def get_saved(user_id):
    conn = sqlite3.connect("Databases/posts.db")
    cur = conn.cursor()
    conn2 = sqlite3.connect("Databases/users.db")
    cur2 = conn2.cursor()

    sql = f'''
    SELECT saved FROM UsersTable
    WHERE user_id='{user_id}'
    '''
    cur2.execute(sql)
    result = cur2.fetchall()
    post_ids = result[0][0]
    cur2.close()
    conn2.close()
    if not post_ids or post_ids == '':
        return []
    post_idSequence = post_ids.split(' ')
    if len(post_idSequence) > 0 and post_idSequence[len(post_idSequence) - 1] == '':
        post_idSequence.pop()
    records = []
    for post_id in post_idSequence:
        sql = f'''
        SELECT * FROM PostsTable
        WHERE post_id='{post_id}'
        '''
        cur.execute(sql)
        record = cur.fetchall()
        if len(record) == 0:
            print(post_id)
        else:
            records.append(record[0])
    cur.close()
    conn.close()
    return records

def get_all_posts(user_id='', sort='newest'):
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
        sql = '''SELECT * FROM PostsTable ORDER BY timestamp'''
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
            cur.execute(sql)
            record = cur.fetchall()
            if len(record) == 0:
                print(post_id)
            else:
                if sort == 'newest':
                    records.append(record[0])
                elif sort == 'oldest':
                    records.insert(0, record[0])
                elif sort == 'popular':
                    index = 0
                    for row in records:
                        if row[11] >= record[0][11]:
                            break
                        index += 1
                    records.insert(index, record[0])
        cur.close()
        conn.close()
        return records

def get_posts_from_query(query):
    conn = sqlite3.connect("Databases/posts.db")
    cur = conn.cursor()

    sql = f'''SELECT * FROM PostsTable
    WHERE title LIKE '%{query}%' OR post LIKE '%{query}%'
    ORDER BY
        CASE
            WHEN post LIKE '%{query}%' THEN 1
            WHEN title LIKE '%{query}%' THEN 2
            ELSE 3
        END
    '''

    cur.execute(sql)
    result = cur.fetchall()

    return result

def get_posts(genres, helplist):
    conn = sqlite3.connect("Databases/posts.db")
    cur = conn.cursor()

    genre_condition = ""
    help_condition = ""
    if len(genres) > 0:
        for genre in genres:
            genre_condition += "music_genre='" + genre + "' OR "
        genre_condition = genre_condition[:(len(genre_condition) - 4)]
        print(genre_condition)
    if len(helplist) > 0:
        for help in helplist:
            help_condition += "help_needed='" + help + "' OR "
        help_condition = help_condition[:(len(help_condition) - 4)]

    sql = f''''''

    if len(genres) == 0 and len(helplist) == 0:
        return get_all_posts()
    elif len(genres) == 0 and len(helplist) != 0:
        sql = f'''
        SELECT * FROM PostsTable
        WHERE {help_condition}
        ORDER BY TIMESTAMP'''
    elif len(genres) != 0 and len(helplist) == 0:
        sql = f'''
        SELECT * FROM PostsTable
        WHERE {genre_condition}
        ORDER BY TIMESTAMP'''
    else:
        sql = f'''
        SELECT * FROM PostsTable
        WHERE ({genre_condition}) AND ({help_condition})
        ORDER BY TIMESTAMP'''
    
    print(sql)
    cur.execute(sql)
    records = cur.fetchall()
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

def get_all_comments(post_id, records=[], reply_id=0):
    conn = sqlite3.connect("Databases/forums.db")
    cur = conn.cursor()

    if reply_id == 0:
        records.clear()

    sql = f''''''
    if reply_id == 0:
        sql = f'''
            SELECT * FROM F{post_id}
            WHERE reply_id={reply_id}
            ORDER BY likes DESC
            '''
    else:
        sql = f'''
            SELECT * FROM F{post_id}
            WHERE reply_id={reply_id}
            ORDER BY timestamp
            '''

    cur.execute(sql)
    records_temp = cur.fetchall()

    for row in records_temp:
        records.append(row)
        get_all_comments(post_id, records, row[0])

    cur.close()
    conn.close()
    
    return records

def get_posts_from_projects(project_id):
    conn = sqlite3.connect("Databases/projects.db")
    cur = conn.cursor()

    conn2 = sqlite3.connect("Databases/posts.db")
    cur2 = conn2.cursor()

    sql = f'''
    SELECT post_ids FROM ProjectsTable
    WHERE project_id='{project_id}'
    '''

    cur.execute(sql)
    result = cur.fetchall()
    if len(result) == 0 or len(result[0]) == 0:
        return '404'
    post_ids = result[0][0]

    post_idSequence = post_ids.split(' ')
    if len(post_idSequence) > 0 and post_idSequence[len(post_idSequence) - 1] == '':
        post_idSequence.pop()
    records = []
    for post_id in post_idSequence:
        sql2 = f'''
        SELECT * FROM PostsTable
        WHERE post_id='{post_id}'
        '''
        cur2.execute(sql2)
        record = cur2.fetchall()
        if len(record) > 0:
            records.append(record[0])
    cur.close()
    conn.close()
    cur2.close()
    conn2.close()
    return records

def get_applications_from_project(project_id):
    conn = sqlite3.connect("Databases/applications.db")
    cur = conn.cursor()

    sql = f'''
    SELECT * FROM ApplicationsTable
    WHERE project_id='{project_id}'
    '''

    cur.execute(sql)
    records = cur.fetchall()

    return records

def get_notifications_from_user(user_id):
    conn = sqlite3.connect("Databases/notifications.db")
    cur = conn.cursor()

    table_name = 'U' + str(user_id)

    sql = f'''SELECT * FROM {table_name} ORDER BY timestamp'''

    cur.execute(sql)
    records = cur.fetchall()

    return records

def get_chats_from_project(project_id):
    conn = sqlite3.connect("Databases/chat.db")
    cur = conn.cursor()

    table_name = 'P' + str(project_id)
    sql = f'''SELECT * FROM {table_name} ORDER BY timestamp'''

    cur.execute(sql)
    records = cur.fetchall()

    return records

def get_updates_from_project(project_id):
    conn = sqlite3.connect("Databases/updates.db")
    cur = conn.cursor()

    table_name = 'P' + str(project_id)
    sql = f'''SELECT * FROM {table_name} ORDER BY timestamp'''

    cur.execute(sql)
    records = cur.fetchall()

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

def get_user(user_id):
    conn = sqlite3.connect("Databases/users.db")
    cur = conn.cursor()
    sql = f'''
    SELECT * FROM UsersTable
    WHERE user_id='{user_id}'
    '''
    cur.execute(sql)
    result = cur.fetchall()
    cur.close()
    conn.close()
    if len(result) == 0:
        return '404'
    return result[0]

def get_post(post_id):
    conn = sqlite3.connect("Databases/posts.db")
    cur = conn.cursor()

    sql = f'''
    SELECT * FROM PostsTable
    WHERE post_id='{post_id}'
    '''

    cur.execute(sql)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()

    if (len(result) == 0 or len(result[0]) == 0):
        return '404'
    post = result[0]

    return post

def get_project(project_id):
    conn = sqlite3.connect("Databases/projects.db")
    cur = conn.cursor()

    sql = f'''
    SELECT * FROM ProjectsTable
    WHERE project_id='{project_id}'
    '''

    cur.execute(sql)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()

    if (len(result) == 0 or len(result[0]) == 0):
        return '404'
    project = result[0]

    return project

def get_deleted_project(project_id):
    conn = sqlite3.connect("Databases/deleted-projects.db")
    cur = conn.cursor()

    sql = f'''
    SELECT * FROM DeletedProjectsTable
    WHERE project_id='{project_id}'
    '''

    cur.execute(sql)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()

    if (len(result) == 0 or len(result[0]) == 0):
        return '404'
    project = result[0]

    return project

def get_all_liked(user_id):
    conn = sqlite3.connect("Databases/users.db")
    cur = conn.cursor()

    sql = f'''
    SELECT comments_liked, posts_liked FROM UsersTable
    WHERE user_id='{user_id}'
    '''

    cur.execute(sql)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()

    return {'comments': result[0][0], 'posts': result[0][1]}

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

def update_bio_from_user(user_id, bio):
    conn = sqlite3.connect("Databases/users.db")
    cur = conn.cursor()

    sql = f'''
    UPDATE UsersTable
    SET bio='{bio}'
    WHERE user_id='{user_id}';
    '''
    try:
        cur.execute(sql)
        conn.commit()
    except:
        print('update_bio_from_user error')
    cur.close()
    conn.close()

    return 'done'

def update_social_from_user(user_id, social, handle):
    conn = sqlite3.connect("Databases/users.db")
    cur = conn.cursor()

    sql = f'''
    UPDATE UsersTable
    SET {social}='{handle}'
    WHERE user_id='{user_id}';
    '''
    try:
        cur.execute(sql)
        conn.commit()
    except:
        print('update_social_from_user error')
    cur.close()
    conn.close()

    return 'done'

def update_activity_from_project(project_id, username, is_active):
    conn = sqlite3.connect("Databases/projects.db")
    cur = conn.cursor()

    sql = f'''
    SELECT active FROM ProjectsTable
    WHERE project_id='{project_id}'
    '''
    cur.execute(sql)
    records = cur.fetchall()

    usr_str = username + ' '
    if is_active:
        if usr_str not in records[0][0]:
            update_activity_from_project(project_id, username, False)
            sql = f'''
            UPDATE ProjectsTable
            SET active=active || '{usr_str}'
            WHERE project_id='{project_id}'
            '''
            cur.execute(sql)
            conn.commit()
    else:
        active_replacement = records[0][0].replace(usr_str, '')
        sql = f'''
        UPDATE ProjectsTable
        SET active='{active_replacement}'
        WHERE project_id='{project_id}'
        '''
        cur.execute(sql)
        conn.commit()
    cur.close()
    conn.close()

def decide_application(application_id, accept):
    conn = sqlite3.connect("Databases/applications.db")
    cur = conn.cursor()
    conn2 = sqlite3.connect("Databases/projects.db")
    cur2 = conn2.cursor()
    conn3 = sqlite3.connect("Databases/users.db")
    cur3 = conn3.cursor()

    sql = f'''
    SELECT project_id, username FROM ApplicationsTable
    WHERE application_id='{application_id}'
    '''
    cur.execute(sql)
    records = cur.fetchall()
    member_to_add = ' ' + records[0][1]
    if accept:
        sql2 = f'''
        UPDATE ProjectsTable
        SET usernames=usernames || '{member_to_add}'
        WHERE project_id='{records[0][0]}'
        '''
        print(sql2)
        cur2.execute(sql2)
        conn2.commit()
        update_projects_from_user(get_user_id(records[0][1]), records[0][0])
        message = 'Your application for ' + get_project(records[0][0])[2] + ' has been accepted!'
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        add_notification(get_user_id(records[0][1]), 'app-accept', records[0][0], message, 'project/' + str(records[0][0]))
    else:
        message = 'Your application for ' + get_project(records[0][0])[2] + ' has been denied.'
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        add_notification(get_user_id(records[0][1]), 'app-deny', records[0][0], message, '')
    sql = f'''
    DELETE FROM ApplicationsTable
    WHERE application_id='{application_id}'
    '''
    cur.execute(sql)
    conn.commit()
    
    cur.close()
    conn.close()
    cur2.close()
    conn2.close()

    return 'done'

def application_exists(project_id, username):
    conn = sqlite3.connect("Databases/applications.db")
    cur = conn.cursor()

    sql = f'''
    SELECT * FROM ApplicationsTable
    WHERE project_id='{project_id}' and username='{username}'
    '''

    cur.execute(sql)
    records = cur.fetchall()

    cur.close()
    conn.close()

    return (len(records) > 0)

def save_post(user_id, post_id, reaction):
    try:
        conn = sqlite3.connect("Databases/users.db")
        cur = conn.cursor()

        sql = f'''
        SELECT saved FROM UsersTable
        WHERE user_id='{user_id}'
        '''

        cur.execute(sql)
        result = cur.fetchall()

        if str(post_id) in result[0][0] and reaction == -1:
            saved_replacement = result[0][0].replace(str(post_id) + ' ', '')
            sql2 = f'''
            UPDATE UsersTable
            SET saved='{saved_replacement}'
            WHERE user_id='{user_id}';
            '''

            cur.execute(sql2)
            conn.commit()
            
        elif str(post_id) not in result[0][0] and reaction == 1:
            post_idStr = str(post_id) + ' '
            sql2 = f'''
            UPDATE UsersTable
            SET saved=saved || '{post_idStr}'
            WHERE user_id='{user_id}';
            '''

            cur.execute(sql2)
            conn.commit()

        cur.close()
        conn.close()
    except Exception as e:
        print(e)

    return 'done'

def like_comment(user_id, post_id, comment_id, reaction):
    try:
        conn2 = sqlite3.connect("Databases/users.db")
        cur2 = conn2.cursor()

        sql2 = f'''
        SELECT comments_liked FROM UsersTable
        WHERE user_id='{user_id}'
        '''

        cur2.execute(sql2)
        result = cur2.fetchall()

        if str(comment_id) in result[0][0] and reaction == -1:
            conn = sqlite3.connect("Databases/forums.db")
            cur = conn.cursor()
            comments_replacement = result[0][0].replace(str(comment_id) + ' ', '')
            sql2 = f'''
            UPDATE UsersTable
            SET comments_liked='{comments_replacement}'
            WHERE user_id='{user_id}';
            '''

            cur2.execute(sql2)
            conn2.commit()

            sql = f'''
            UPDATE F{post_id}
            SET likes=likes-1
            WHERE comment_id = '{comment_id}';
            '''
            
        elif str(comment_id) not in result[0][0] and reaction == 1:
            conn = sqlite3.connect("Databases/forums.db")
            cur = conn.cursor()
            comment_idStr = str(comment_id) + ' '
            sql2 = f'''
            UPDATE UsersTable
            SET comments_liked=comments_liked || '{comment_idStr}'
            WHERE user_id='{user_id}';
            '''

            cur2.execute(sql2)
            conn2.commit()

            sql = f'''
            UPDATE F{post_id}
            SET likes=likes+1
            WHERE comment_id = '{comment_id}';
            '''

        cur.execute(sql)
        conn.commit()

        cur.close()
        conn.close()
        cur2.close()
        conn2.close()
    except Exception as e:
        print(e)

    return 'done'

def like_post(user_id, post_id, reaction):
    try:
        conn2 = sqlite3.connect("Databases/users.db")
        cur2 = conn2.cursor()

        sql2 = f'''
        SELECT posts_liked FROM UsersTable
        WHERE user_id='{user_id}'
        '''

        cur2.execute(sql2)
        result = cur2.fetchall()

        if str(post_id) in result[0][0] and reaction == -1:
            conn = sqlite3.connect("Databases/posts.db")
            cur = conn.cursor()
            posts_replacement = result[0][0].replace(str(post_id) + ' ', '')
            sql2 = f'''
            UPDATE UsersTable
            SET posts_liked='{posts_replacement}'
            WHERE user_id='{user_id}';
            '''

            cur2.execute(sql2)
            conn2.commit()

            sql = f'''
            UPDATE PostsTable
            SET likes=likes-1
            WHERE post_id = '{post_id}';
            '''
            
        elif str(post_id) not in result[0][0] and reaction == 1:
            conn = sqlite3.connect("Databases/posts.db")
            cur = conn.cursor()
            post_idStr = str(post_id) + ' '
            sql2 = f'''
            UPDATE UsersTable
            SET posts_liked=posts_liked || '{post_idStr}'
            WHERE user_id='{user_id}';
            '''

            cur2.execute(sql2)
            conn2.commit()

            sql = f'''
            UPDATE PostsTable
            SET likes=likes+1
            WHERE post_id = '{post_id}';
            '''

        cur.execute(sql)
        conn.commit()
        cur2.close()
        conn2.close()
    except Exception as e:
        print(e)

    return 'done'

def remove_member(username, project_id, is_self=False):
    conn = sqlite3.connect("Databases/projects.db")
    cur = conn.cursor()
    conn2 = sqlite3.connect("Databases/users.db")
    cur2 = conn2.cursor()

    sql = f'''
    SELECT usernames, title, requested FROM ProjectsTable
    WHERE project_id='{project_id}'
    '''

    cur.execute(sql)
    records = cur.fetchall()
    usernames = records[0][0]
    title = records[0][1]
    requested = records[0][2]
    usernames_replacement = ''
    if username == usernames.split(' ')[0]:
        usernames_replacement = usernames.replace(username + ' ', '')
    else:
        usernames_replacement = usernames.replace(' ' + username, '')
    
    sql = f'''
    UPDATE ProjectsTable
    SET usernames='{usernames_replacement}'
    WHERE project_id='{project_id}';
    '''

    cur.execute(sql)
    conn.commit()
    requested_replacement = requested.replace(username + ' ', '')

    sql = f'''
    UPDATE ProjectsTable
    SET requested='{requested_replacement}'
    WHERE project_id='{project_id}';
    '''

    cur.execute(sql)
    conn.commit()
    user_id = get_user_id(username)

    sql2 = f'''
    SELECT projects FROM UsersTable
    WHERE user_id='{user_id}'
    '''

    cur2.execute(sql2)
    projects = cur2.fetchall()[0][0]
    projects_replacement = projects.replace(str(project_id) + ' ', '')

    sql2 = f'''
    UPDATE UsersTable
    SET projects='{projects_replacement}'
    WHERE user_id='{user_id}';
    '''

    cur2.execute(sql2)
    conn2.commit()

    cur.close()
    conn.close()
    cur2.close()
    conn2.close()
    if not is_self:
        message = 'You have been removed from project: ' + title + '.'
        add_notification(user_id, 'remove', project_id, message, '/contest/' + str(project_id))

    return 'done'

def upgrade_member(username, project_id):
    conn = sqlite3.connect("Databases/projects.db")
    cur = conn.cursor()

    sql = f'''
    SELECT usernames, title FROM ProjectsTable
    WHERE project_id='{project_id}'
    '''

    cur.execute(sql)
    records = cur.fetchall()
    usernames = records[0][0]
    title = records[0][1]
    current_owner = usernames.split(' ')[0]
    u_str1 = usernames.replace(current_owner + ' ', 'bad_code ')
    u_str2 = u_str1.replace(' ' + username, ' ' + current_owner)
    usernames_replacement = u_str2.replace('bad_code ', username + ' ')

    sql = f'''
    UPDATE ProjectsTable
    SET usernames='{usernames_replacement}'
    WHERE project_id='{project_id}';
    '''

    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    message = 'You have been selected as owner in project: ' + title + '.'
    add_notification(get_user_id(username), 'upgrade', project_id, message, '/project/' + str(project_id))

    return 'done'

def request_member(username, project_id):
    if not check_valid_username(username):
        return 'invalid'
    conn = sqlite3.connect("Databases/projects.db")
    cur = conn.cursor()

    sql = f'''
    SELECT title, usernames FROM ProjectsTable
    WHERE project_id='{project_id}'
    '''

    cur.execute(sql)
    records = cur.fetchall()
    title = records[0][0]
    usernames = records[0][1]
    if username in usernames:
        return 'in-project'
    user_id = get_user_id(username)
    message = 'The project ' + title + ' has requested you to join.'
    add_notification(user_id, 'project-request', project_id, message, '/acceptproject/' + str(project_id))
    member_to_add = username + ' '
    
    sql = f'''
    UPDATE ProjectsTable
    SET requested=requested || '{member_to_add}'
    WHERE project_id='{project_id}'
    '''

    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

    return 'done'

def accept_project(username, project_id):
    conn = sqlite3.connect("Databases/projects.db")
    cur = conn.cursor()

    sql = f'''
    SELECT usernames, requested FROM ProjectsTable
    WHERE project_id='{project_id}'
    '''

    cur.execute(sql)
    records = cur.fetchall()
    if len(records) == 0 or len(records[0]) == 0:
        return '404'
    usernames = records[0][0]
    requested = records[0][1]
    if username in usernames:
        return 'done'
    if username not in requested:
        return '404'
    member_to_add = ' ' + username

    sql = f'''
    UPDATE ProjectsTable
    SET usernames=usernames || '{member_to_add}'
    WHERE project_id='{project_id}'
    '''

    cur.execute(sql)
    conn.commit()

    requested_toReplace = requested.replace(member_to_add, '')

    sql = f'''
    UPDATE ProjectsTable
    SET requested='{requested_toReplace}'
    WHERE project_id='{project_id}'
    '''

    cur.execute(sql)
    conn.commit()

    update_projects_from_user(get_user_id(username), project_id)

    return 'done'

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
        cur.execute(sql)
        result = cur.fetchall()
        project_id = result[0][0]
        username = result[0][1]
        user_id = get_user_id(username)
        sql = f'''
        DELETE FROM PostsTable
        WHERE post_id = '{post_id}'
        '''
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
        cur2.execute(sql2)
        conn2.commit()
    except Exception as e:
        print('error in updating users.db', e)

    cur2.close()
    conn2.close()

    conn3 = sqlite3.connect("Databases/forums.db")
    cur3 = conn3.cursor()

    try:
        sql3 = f'''DROP TABLE IF EXISTS F{post_id};'''
        cur3.execute(sql3)
        conn3.commit()
    except Exception as e:
        print('error in deleting from forums.db', e)

    if (os.path.isfile("static/uploads/img" + str(post_id) + ".jpg")):
        os.remove("static/uploads/img" + str(post_id) + ".jpg")
    if (os.path.isfile("static/uploads/audio" + str(post_id) + ".mp3")):
        os.remove("static/uploads/audio" + str(post_id) + ".mp3")
    if (os.path.isfile("static/uploads/video" + str(post_id) + ".mp4")):
        os.remove("static/uploads/video" + str(post_id) + ".mp4")
    
    if project_id == 0:
        return 'done'
    
    conn4 = sqlite3.connect("Databases/projects.db")
    cur4 = conn4.cursor()

    try:
        sql4 = f'''
        SELECT post_ids FROM ProjectsTable
        WHERE project_id='{project_id}'
        '''
        cur4.execute(sql4)
        result4 = cur4.fetchall()
        post_ids = result4[0][0]
        post_idsReplacement = post_ids.replace(str(post_id) + ' ', '')
        sql4 = f'''
        UPDATE ProjectsTable
        SET post_ids='{post_idsReplacement}'
        WHERE project_id='{project_id}';
        '''
        cur4.execute(sql4)
        conn4.commit()
    except Exception as e:
        print('error in updating projects.db', e)
    
    cur4.close()
    conn4.close()

    return 'done'

def delete_project(project_id):
    conn = sqlite3.connect("Databases/projects.db")
    cur = conn.cursor()
    conn2 = sqlite3.connect("Databases/deleted-projects.db")
    cur2 = conn2.cursor()
    conn3 = sqlite3.connect("Databases/users.db")
    cur3 = conn3.cursor()

    sql = f'''
    SELECT * FROM ProjectsTable
    WHERE project_id='{project_id}'
    '''

    cur.execute(sql)
    records = cur.fetchall()

    print(records)

    sql2 = f'''
    INSERT INTO DeletedProjectsTable(project_id, usernames, title,
        desc, post_ids, chat_id, requested)
    VALUES(?,?,?,?,?,?,?)
    '''

    cur2.execute(sql2, (records[0][0], records[0][1], records[0][2], records[0][3], records[0][4],
        records[0][5], records[0][6]))
    conn2.commit()

    user_id = get_user_id(records[0][1])
    sql3 = f'''
    SELECT projects FROM UsersTable
    WHERE user_id='{user_id}'
    '''

    cur3.execute(sql3)
    records2 = cur3.fetchall()
    projects_replacement = records2[0][0].replace(str(project_id) + ' ', '')
    sql3 = f'''
    UPDATE UsersTable
    SET projects='{projects_replacement}'
    WHERE user_id='{user_id}';
    '''

    cur3.execute(sql3)
    conn3.commit()

    sql = f'''
    DELETE FROM ProjectsTable
    WHERE project_id='{project_id}'
    '''

    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    cur2.close()
    conn2.close()
    cur3.close()
    conn3.close()

    return 'done'