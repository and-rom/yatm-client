#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import configparser
import os
import re
import socket
import threading
import sys
import json
import pprint

BUFF = 1024
HOST = '127.0.0.1'# must be input parameter @TODO
PORT = 44441 # must be input parameter @TODO

class Sentry:
	config = configparser.ConfigParser()
	probes = []
	values = []
	pp = pprint.PrettyPrinter(indent=4)
        # инициализация, получение параметров из файла конфигурации
	def __init__ (self):
		self.config.read('config.ini')
		for section in self.config.sections():
			probe = {}
			probe['name'] = section
			for option in self.config.options(section):
				probe[option]=self.config.get(section,option)
			self.probes.append(probe)

        # опрос датчиков
	def inspect (self):
		self.values = []
		for probe in self.probes:
			value={}
			value['name']=probe['name']
			rawoutput = self.execute(probe['command'])
			output = self.bmcontrol(rawoutput)
			value['value']=str(output)
			self.values.append(value)

	# вызов внешней программы для получение значения датчика
	def execute (self,command):
		result = os.popen(command[1:len(command)-1]).read()
		return result

	# обработка результата выполения команды bmcontrol
	def bmcontrol(self, rawoutput):
		re1 = "(Device not plugged)|(Error GET_TEMPERATURE)"
		rg = re.compile(re1,re.IGNORECASE|re.DOTALL)
		m = rg.search(rawoutput)	
		if not m:
			return float(rawoutput)
		else:

			return "err"
	# формирование json ответа
	def json (self,datatype):
		if  (datatype=='values'):
			target=self.values
		elif (datatype=='probes'):
			target=self.probes
		result=json.dumps(target)
		return result

m = Sentry()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(5)

try:
	closed=True
	while True:
		if closed:
			conn, addr = s.accept()
		data = conn.recv(BUFF)
		if not data:
			conn.close()
		else:
			if (data==b'values'):
				m.inspect()
				conn.send(m.json(data.decode()).encode())
				closed=False
			elif (data==b'probes'):
				conn.send(m.json(data.decode()).encode())
				closed=False
			elif data==b'close':
				conn.send(b'close')
				conn.close()
				closed=True
			else:
				conn.send(b'err')
				closed=False
except (KeyboardInterrupt, SystemExit):
	try:
		conn
	except NameError:
		exit()
	else:
		conn.close()
		exit()
