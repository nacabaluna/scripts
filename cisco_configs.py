#!/usr/bin/python

from ciscoconfparse import CiscoConfParse
import re, sys, getpass, pexpect, os

def ssh_command (user, host, password):

    """This runs a command on the remote host. This could also be done with the
pxssh class, but this demonstrates what that class does at a simpler level.
This returns a pexpect.spawn object. This handles the case when you try to
connect to a new host and ssh asks you if you want to accept the public key
fingerprint and continue connecting. """

    ssh_newkey = 'Are you sure you want to continue connecting'
    child = pexpect.spawn('ssh -l %s %s'%(user, host), timeout= 60)
    i = child.expect([pexpect.TIMEOUT, ssh_newkey, '[Pp]assword:'])
    if i == 0: # Timeout
        print 'ERROR!'
        print 'SSH could not login. Here is what SSH said:'
        print child.before, child.after
        return None
    if i == 1: # SSH does not have the public key. Just accept it.
        child.sendline ('yes')
        child.expect ('[Pp]assword:')
        i = child.expect([pexpect.TIMEOUT, '[Pp]assword: '])
        if i == 0: # Timeout
            print 'ERROR!'
            print 'SSH could not login. Here is what SSH said:'
            print child.before, child.after
            return None       
    child.sendline(password)
    return child


def hash_objects(objects, config):
  object_lists = {}
  for entry in objects:
   children = config.find_children(entry)
   #obj_name = children[0].split()
   #object_lists[obj_name[2]] = children[1:]
   object_lists[children[0]] = children[1:]
  return object_lists

def find_value(value, object_lists):
  matches = []
  search_string = re.compile(value)
  for k,v in object_lists.iteritems():
    for i in v:
      if search_string.search(i):
        matches.append(k)
  return matches

def get_object_network( config ):
  objects = config.find_lines("^object network")
  return hash_objects(objects,config)

def get_object_service( parse ):
  objects = parse.find_lines("^object service")
  return hash_objects(objects,config)
 
def get_objectgroup_network( config ):
  objects = config.find_lines("^object-group network")
  return hash_objects(objects,config)

def get_objectgroup_service( config ):
  objects = config.find_lines("^object-group service")
  return hash_objects(objects,config)

def find_network_value( value, config ):
  networkObject = get_object_network( config )
  networkObject_group = get_objectgroup_network( config )
  matches = find_value(value, networkObject)
  matches = matches + find_value(value, networkObject_group)
  return matches

def find_service_value( value, config ):
  serviceObject = get_object_service( config )
  serviceObject_group = get_objectgroup_service( config )
  matches = find_value(value, serviceObject)
  matches = matches + find_value(value, serviceObject_group)
  return matches

def get_login():
  user = raw_input('User: ')
  password = getpass.getpass('Password: ')
  enable = getpass.getpass('Enable: ')
  return user,password,enable

def push_commands(session,prompt,commands):
  ### Pushes the cisco commands in an array, inputs are the pexpect ssh object and the commands to run
  session.sendline("\r\r")
  for command in commands:
    session.expect(prompt)
    session.sendline(command + "\r")
  session.expect(prompt)
  session.sendline("exit\r")
  return 0 

def grab_configs(hostname):
  user,password,enable = get_login()
  myfile = open(hostname,'w')
  child = ssh_command (user, hostname, password)
  prompt = hostname + "#"
  print "===", prompt
  response = child.expect ([hostname + '>', hostname + '#'])
  if response==0:
     child.sendline("enable\r")
     child.expect("Password: ")
     child.sendline(enable + "\r")
  child.logfile = myfile
  commands = ['terminal pager 0\r','terminal length 0\r','show running-config\r']
  push_commands(child,prompt,commands)
  child.expect(pexpect.EOF)
  myfile.close()
  return 0
## TEST CODE ##

###
