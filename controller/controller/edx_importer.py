#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
Script used to upload the data from the sql dumps created by edx into the
db used by the messaging system
"""

import multiprocessing
import mysql.connector
from mysql.connector import errorcode
import psycopg2
import os
import re
import time
import datetime
import subprocess
import json
import codecs
from collections import OrderedDict
from settings import DATABASES


#Root folder of the edx courses data
EDX_DATA_ROOT='/home/ceh/code/github/dms/data/idbx-2017-10-30'

#Maximum number of process to run
NUM_PROCESS = 10


#Dictionary used to determine how the edx data will be uploaded. The dictionary
#uses the suffix of the sql dump as keys that point to another dictionary
#containing the name of the table to be updated and the values used from each
#entry in the sql dump. If a value in the dump is not relevant because it has
#been deprecated or marked as not used in edx then @dummy is used to skip it
#from loading into the table
DATA_TABLES_INFO = OrderedDict([
    ('-auth_user-prod-analytics.sql', {'table': 'auth_user',
                                  'values': '(id,username,first_name,last_name,email,password,is_staff,is_active,is_superuser,last_login,date_joined)'}),
    ('-auth_userprofile-prod-analytics.sql', {'table': 'auth_userprofile',
                                         'values': '(id,user_id,name,@dummy,@dummy,meta,@dummy,gender,@dummy,year_of_birth,level_of_education,goals,allow_certificate,country,city,bio,profile_image_uploaded_at)'}),
    ('-student_courseenrollment-prod-analytics.sql', {'table': 'student_courseenrollment',
                                                 'values': '(id,user_id,course_id,created,is_active,mode)'}),
    ('-user_id_map-prod-analytics.sql', {'table': 'user_id_map',
                                    'values': '(hash_id,id,username)'}),
    ('-student_anonymoususerid-prod-analytics.sql', {'table': 'student_anonymoususerid',
                                                'values': '(id,user_id,anonymous_user_id,course_id)'}),
    ('-student_languageproficiency-prod-analytics.sql', {'table': 'student_languageproficiency',
                                                    'values': '(id,user_profile_id,code)'}),
    ('-courseware_studentmodule-prod-analytics.sql', {'table': 'courseware_studentmodule',
                                                 'values': '(id,module_type,module_id,student_id,state,grade,created,modified,max_grade,done,course_id)'}),
    ('-grades_persistentcoursegrade-prod-analytics.sql', {'table': 'grades_persistentcoursegrade',
                                                     'values': '(course_id,user_id,grading_policy_hash,percent_grade,letter_grade,passed_timestamp,created,modified)'}),
    ('-grades_persistentsubsectiongrade-prod-analytics.sql', {'table': 'grades_persistentsubsectiongrade',
                                                         'values': '(course_id,user_id,usage_key,earned_all,possible_all,earned_graded,possible_graded,first_attempted,created,modified)'}),
    ('-certificates_generatedcertificate-prod-analytics.sql', {'table': 'certificates_generatedcertificate',
                                                          'values': '(id,user_id,download_url,grade,course_id,`key`,@dummy,status,verify_uuid,download_uuid,name,created_date,modified_date,error_reason,mode)'}),
    ('-student_courseaccessrole-prod-analytics.sql', {'table': 'student_courseaccessrole',
                                                 'values': '(@dummy,course_id,user_id,role)'})])


#MySQL connection configuration
CONFIG_EDX = {
  'user': DATABASES['edx']['USER'],
  'password': DATABASES['edx']['PASSWORD'],
  'host': DATABASES['edx']['HOST'],
  'database': DATABASES['edx']['NAME'],
  'raise_on_warnings': False,
  'autocommit': True,
  'allow_local_infile': True,
  'pool_size': max(NUM_PROCESS,5)
}

#Postgres connection configuration
CONFIG_DEFAULT = {
  'user': DATABASES['default']['USER'],
  'password': DATABASES['default']['PASSWORD'],
  'host': DATABASES['default']['HOST'],
  'dbname': DATABASES['default']['NAME'],
}




def import_data(file, table, values):
    """
    Function used to import data from a sql dump into a table in the db
    parm: file, path of the sql dump source file
    parm: table, name of the table to updated in the db
    parm: values, values from the sql dump that will be uploaded
    """
    try:
        cnx = mysql.connector.connect(**CONFIG_EDX)
        cnx.get_warnings = True
        cursor = cnx.cursor()
        while True:
            try:
                for result in cursor.execute("load data local infile '{0}' ignore into table {1}" \
                             " character set utf8 ignore 1 lines {2}".format(file,
                                                                 table, values), multi=True):
                  print "File {0}, rows affected: {1}, warnings: {2}".format(file, result.rowcount, result.fetchwarnings())
                cnx.commit()
                break
            except mysql.connector.Error as exec_err:
                print("Error {0} trying to load file {1}. Retrying ...".format(exec_err, file))
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print("Error {0} trying to load file {1}".format(err, file))
    finally:
        cursor.close()
        cnx.close()






# Process the course metadata
running_processes = []  # processes queue
active_courses = []
cutoff_time = datetime.datetime.now() - datetime.timedelta(days=7)
try:
    conn = psycopg2.connect("dbname={0} user={1} host={2} password={3}".format(
        CONFIG_DEFAULT['dbname'], CONFIG_DEFAULT['user'],
        CONFIG_DEFAULT['host'], CONFIG_DEFAULT['password']
    ))
    cur = conn.cursor()
    for root, dirs, files in os.walk(EDX_DATA_ROOT):  # search for the sql files
        for file in files:
            # if file name matches wanted file pattern process the file
            suffix_match = re.search(r'(.+)-course.*-analytics.json', file, re.I)
            if suffix_match is not None:
                try:
                    file_name = suffix_match.group(1)
                    course_name = file_name.replace('-','+')
                    course_file = os.path.join(root, file)
                    course_data = json.load(codecs.open(course_file, 'r', 'utf-8-sig'))
                    course_key = "block-v1:{0}+type@course+block@course".format(course_name)
                    course_start_date = course_data[course_key]['metadata']['start']
                    course_end_date = course_data[course_key]['metadata']['end']
                    display_name = course_data[course_key]['metadata']['display_name']
                    enddate = datetime.datetime.strptime(course_end_date, '%Y-%m-%dT%H:%M:%SZ')
                    if enddate > cutoff_time:
                        num_sections = int(subprocess.check_output("cat {0} |grep graded|wc -l".format(course_file), shell=True))
                        if 'language' in course_data[course_key]['metadata']:
                            lang = course_data[course_key]['metadata']['language']
                        else:
                            lang = subprocess.check_output("grep -A2 '\"transcripts\": ' {0} | head -2 | tail -1 | cut -d':' -f 1".format(course_file), shell=True).strip().replace('"','')
                        cur.execute("select * from control_panel_course where id='course-v1:{0}';".format(course_name))
                        if len(cur.fetchall()) == 0:
                            cur.execute("insert into control_panel_course(id, is_active, num_section, language, name, start_date, end_date) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                        ("course-v1:{0}".format(course_name), False, num_sections, lang, display_name, course_start_date, course_end_date))
                            conn.commit()
                        active_courses.append(file_name)
                except Exception, ce:
                    print "ERROR: Unable to process metadata for {0} check file {1}".format(course_name, course_file), ce
    cur.close()
    conn.close()
except Exception, e:
    print "ERROR: Unable to connect to postgresql to load course metadata ", e
    exit(1)

#Process the data, search for relevant files and upload the data to the
#appropriate table
if len(active_courses) == 0:
    print "No active courses detected exiting ..."
    exit(0)

running_processes = [] #processes queue
course_re = '(' + '|'.join(active_courses) + ')'
for file_re in DATA_TABLES_INFO.keys():
    for root, dirs, files in os.walk(EDX_DATA_ROOT): #search for the sql files
        for file in files:
            #if file name matches wanted file pattern process the file
            suffix_match = re.search(file_re, file, re.I)
            if suffix_match is not None and re.search(course_re, file, re.I):
                #Get info of table to update
                table_info = DATA_TABLES_INFO[file_re]

                #Get full path of the data file
                data_file = os.path.join(root, file)
                #If max process allowed is reached wait for a spot to become available
                while len(running_processes) == NUM_PROCESS:
                    time.sleep(5)
                    for p in running_processes:
                        if not p.is_alive():
                            running_processes.remove(p)
                #Process data file in a new process
                new_p = multiprocessing.Process(target=import_data,
                                                args=(data_file,
                                                      table_info['table'],
                                                      table_info['values'],))
                new_p.start()
                running_processes.append(new_p)

#Wait for the remaining processes to finish
for p in running_processes:
    p.join()

#Update upload date in DB
try:
    conn = psycopg2.connect("dbname={0} user={1} host={2} password={3}".format(
        CONFIG_DEFAULT['dbname'], CONFIG_DEFAULT['user'],
        CONFIG_DEFAULT['host'], CONFIG_DEFAULT['password']
    ))
    cur = conn.cursor()
    cur.execute("insert into control_panel_updatelog(last_update) VALUES(%s);", (datetime.datetime.now(),))
    conn.commit()
    cur.close()
    conn.close()
except Exception, e:
    print "Error updating last DB update date", e

print 'Done!!!!'
