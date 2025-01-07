#!/usr/bin/env python3
import asyncio
import sys
import socket
import string
import json
import random
import threading
import time
from threading import Thread
import db_connect
from collections import Counter
from collections import defaultdict

HOST = "127.0.0.1"
PORT = 6667

NICK = "Butt_BOT"
IDENT = "Bot_BOT_test"
REALNAME = "Bot_BOT"
CHANNEL = "#Trivia"

readbuffer = ""
s=socket.socket( )
s.connect((HOST, PORT))



async def main():
	s.send(bytes("NICK %s\r\n" % NICK, "UTF-8"))
	#s.send(bytes("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME), "UTF-8"))
	s.send(bytes("USER guest 0 * :%s\r\n" % REALNAME, "UTF-8"))
	await asyncio.sleep(10)
	s.send(bytes("JOIN #Trivia\r\n", "UTF-8"))
	
asyncio.run(main())

class CountdownTask:
    def __init__(self):
        self._running = True

    def terminate(self):
        self._running = False

    def run(self,word_list,word_char,word_index,counter_int,points):
        while self._running and counter_int <= len(word_list):
            time.sleep(10)
            if len(word_list) <= 0 or self._running == False:
                break
            word_hint = ""

            if counter_int != len(word_list):
                if word_char[word_index[counter_int]] == " ":
                    counter_int +=1
                    word_list[word_index[counter_int]] = word_char[word_index[counter_int]]
                    counter_int +=1
                else:
                    word_list[word_index[counter_int]] = word_char[word_index[counter_int]]
                    counter_int +=1
            else:
                counter_int = counter_int

            for char in word_list:
                word_hint = word_hint + char
            word_hint = ":" + word_hint

            s.send(bytes("PRIVMSG %s %s \r\n" % (CHANNEL, word_hint), "UTF-8"))
            if points >= 0:
                points = points - 1
            else:
                points = points
            del word_hint

def point_calc(winners,points):

    wins = Counter(winners)

    d = defaultdict(list)
    for key, value in zip(winners, points):
        d[key].append(int(value))

    summed_dict = {key:{"wins":wins.get(key),"total":sum(val)} for key, val in d.items()}

    for key in summed_dict.keys():
        mssg = f"{key} answered {summed_dict.get(key).get('wins')} correct and got {summed_dict.get(key).get('total')} points"
        s.send(bytes("PRIVMSG %s %s \r\n" % (CHANNEL, mssg), "UTF-8"))

    for key in d:
        d[key] = sum(map(int, d[key]))
    #print(d)

    db_connect.score_update(d)


def quiz():
  with open('question.json') as f:
      data = json.load(f)
  random_index = random.sample(range(0, len(data)),3)

  turn = 0
  secret_word = ""
  point_list = []
  winner_list = []

  mssg = ":" + "Welcome to the 3 question quiz - Do your best!!"
  s.send(bytes("PRIVMSG %s %s \r\n" % (CHANNEL, mssg), "UTF-8"))
  time.sleep(5.0)

  while turn < 3:

      guess = ""

      secret_word_list = []
      secret_word_char = []

      if(len(secret_word) == 0):
        question = data[random_index[turn]]["question"]
        question = ":" + question
        s.send(bytes("PRIVMSG %s %s \r\n" % (CHANNEL, question), "UTF-8"))
        del question

        for char in data[random_index[turn]]["answer"]:
            if char == " ":
                secret_word = secret_word + "  "
                secret_word_list.append(" ")
            else:
                secret_word = secret_word + "- "
                secret_word_list.append("- ")
        secret_word = ":" + secret_word

        for char in data[random_index[turn]]["answer"]:
            secret_word_char.append(char)
        answer = ":" + data[random_index[turn]]["answer"]

        counter_int = 0
        points = len(answer)
        hint_word_index = random.sample(range(0, len(secret_word_list)),len(secret_word_list))
        c=CountdownTask()
        repeat_timer = Thread(target = c.run, args =[secret_word_list,secret_word_char,hint_word_index,counter_int,points, ])
        repeat_timer.start()

      readb = ""
      readb = readb+s.recv(1024).decode("UTF-8")
      temp = str.split(readb, "\n")
      readb=temp.pop( )

      for lineb in temp:
          lineb = str.rstrip(lineb)
          lineb = str.split(lineb)

          if(lineb[0] == "PING"):
              s.send(bytes("PONG %s\r\n" % lineb[1], "UTF-8"))

      if(lineb[1] == "PRIVMSG" and lineb[2] == CHANNEL):
          guess = ' '.join(lineb[3:])
          if guess.lower() == answer.lower():
              winner_user = lineb[0].split("!")
              winner_message = winner_user[0] + " - You are correcto-mundo!"
              s.send(bytes("PRIVMSG %s %s \r\n" % (CHANNEL, winner_message), "UTF-8"))
              winner_list.append(winner_user[0])
              point_list.append(points)
              turn += 1
              c.terminate()
              secret_word = ""
              time.sleep(5.0)


  mssg_end = ":" + "The end (Of the quiz)"
  point_calc(winner_list,point_list)
  s.send(bytes("PRIVMSG %s %s \r\n" % (CHANNEL, mssg_end), "UTF-8"))

def top5():
    top_score = db_connect.top()
    for x in top_score:
        s.send(bytes("PRIVMSG %s %s \r\n" % (CHANNEL, x), "UTF-8"))

function_dict = {
    "quiz": quiz,
    "top": top5,
}


def key_check(key):
    if function_dict.__contains__(key):
        return function_dict[key]()
    else:
        return "Wrong_Command"


while 1:
    readbuffer = readbuffer+s.recv(1024).decode("UTF-8")
    print(readbuffer)
    temp = str.split(readbuffer, "\n")
    readbuffer=temp.pop( )

    for line in temp:
        line = str.rstrip(line)
        line = str.split(line)

        if(line[0] == "PING"):
            s.send(bytes("PONG %s\r\n" % line[1], "UTF-8"))

        if(line[1] == "PRIVMSG" and line[2] == CHANNEL):
            for char in line[3]:
                if(char == "!"):
                    command = line[3].split("!")
                    func_argument = command[1]
                    key_check(func_argument)
        if(line[1] == "PRIVMSG" and line[2] == NICK):
            if line[3].lower() == ":register":
                return_msg = db_connect.register(line[4])
                s.send(bytes("PRIVMSG %s %s \r\n" % (CHANNEL, return_msg), "UTF-8"))

        #for index, i in enumerate(line):
            #print(line[index])
