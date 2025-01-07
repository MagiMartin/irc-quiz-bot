import mysql.connector
import string



def register(nick):

    db = mysql.connector.connect(host='localhost', user='***', password='***', database='irc_quiz')
    cursor = db.cursor()

    query = "SELECT nick FROM users"
    cursor.execute(query)
    records = [item[0] for item in cursor.fetchall()]

    for index in range(len(records)):
        if records[index].lower() == nick.lower():
            return ":Nick is in use"
        else:
            add_data = ("INSERT INTO users"
                       "(nick, score) "
                       "VALUES (%s, %s)")
            data = (nick.lower(), "0")
            cursor.execute(add_data, data)
            db.commit()
            return ":Nickname registered"

    cursor.close()
    db.close()


def top():

    db = mysql.connector.connect(host='localhost', user='***', password='***', database='irc_quiz')
    cursor = db.cursor()

    query = "SELECT * FROM users ORDER BY score DESC LIMIT 5"
    cursor.execute(query)
    records = cursor.fetchall()

    top5 = []
    for row in records:
        temp = ":" + row[1] + " " + str(row[2])
        top5.append(temp)

    cursor.close()
    db.close()

    return top5

def score_update(d):

    db = mysql.connector.connect(host='localhost', user='***', password='***', database='irc_quiz')
    cursor = db.cursor()

    for key in d.keys():
       query = "UPDATE users SET score = score+%s WHERE nick=%s"
       score = d.get(key)
       nick = key.split(":")
       cursor.execute(query, (score ,nick[1].lower()))
       db.commit()
    cursor.close()
    db.close()
