from fabric.api import *
import os
import ConfigParser
import time

class bcolors:
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'

  def disable(self):
    self.HEADER = ''
    self.OKBLUE = ''
    self.OKGREEN = ''
    self.WARNING = ''
    self.FAIL = ''
    self.ENDC = ''


# Override the shell env variable in Fabric, so that we don't see 
# pesky 'stdin is not a tty' messages when using sudo
env.shell = '/bin/bash -c'

# Fetch the host to deploy to, from the mapfile, according to its repo and build type
config = ConfigParser.RawConfigParser()
# Force case-sensitivity
config.optionxform = str
cwd = os.getcwd()

# Fetch and import a database dump from remote host
def get_database(drush_cmd, shortname, branch):
  local('mkdir -p ~/sql-dumps')
  print "===> Making a Drupal database backup from %s ..." % env.host
  with settings(hide('stdout', 'warnings', 'stderr'), warn_only=True):
    if run('ps aux | grep drupal_%s.sql.gz | grep -v grep' % shortname).return_code == 0:
      raise SystemExit("Someone was running an SQL dump of this database at the same time! Please wait for their sync to finish and try again in a few moments.")
  run('%s @%s_%s sql-dump | gzip > ~/drupal_%s.sql.gz' % (drush_cmd, shortname, branch, shortname)) 
  time.sleep(5)
  print "===> Fetching the Drupal database backup from %s ..." % env.host
  # Check the database size. This can be helpful to provide info to the user
  # especially if the database dump is very large. Go get a coffee!
  with settings(hide('running', 'stdout')):
    drupal_db_size = run('du -sh ~/drupal_%s.sql.gz' % shortname)
  print bcolors.WARNING + "File size %s, please take this into account if waiting for it to fetch or be imported" % drupal_db_size + bcolors.ENDC

  get('~/drupal_%s.sql.gz' % shortname, '~/sql-dumps/drupal_%s.sql.gz' % shortname)
  run('rm ~/drupal_%s.sql.gz' % shortname)

# Rsync the remote files directory to our local copy.
def get_files(drush_cmd, shortname, url, branch, www_subdir, full):
  if run("%s sa | grep @%s_%s" % (drush_cmd, shortname, branch)).failed:
    raise SystemExit("Couldn't find this site on the remote server")

  print "===> Finding the remote files directory to rsync from..."
  remote_files = run("echo $(%s @%s_%s dd files)" % (drush_cmd, shortname, branch))

  # As above, check the size of the files we're about to sync.
  # Useful to inform the user if it's gonna take a while.
  with settings(hide('running', 'stdout')):
    drupal_file_size = run('du -sh %s/' % remote_files)
  print bcolors.WARNING + "Total size of Drupal files %s, please take this into account if waiting" % drupal_file_size  + bcolors.ENDC

  print "===> Running an rsync of the remote files directory to our local site..."
  with settings(hide('warnings', 'stderr'), warn_only=True):
    if run("stat $(%s @%s_%s dd)/sites/%s" % (drush_cmd, shortname, branch, url)).failed:
      multisite = "default"
    else:
      multisite = url
  # By default, we only rsync down files that are 100k or smaller, to save time. Often we don't *need* all the massive files for dev purposes.
  if full == "1":
    local("rsync -aHPzq %s@%s:%s/ /vagrant/%s/%s/sites/%s/files/" % (env.user, env.host, remote_files, url, www_subdir, multisite))
  else:
    local("rsync -aHPzq --max-size=100K %s@%s:%s/ /vagrant/%s/%s/sites/%s/files/" % (env.user, env.host, remote_files, url, www_subdir, multisite))

  local("sudo chown -R vagrant:www-data /vagrant/%s/%s/sites/%s/files" % (url, www_subdir, multisite))
  local("sudo chmod 2775 /vagrant/%s/%s/sites/%s/files" % (url, www_subdir, multisite))
  local("find /vagrant/%s/%s/sites/%s/files -type d -print0 |xargs -0 -r chmod 2775" % (url, www_subdir, multisite))
  local("find /vagrant/%s/%s/sites/%s/files -type f -print0 |xargs -0 -r chmod 2664" % (url, www_subdir, multisite))

def main(shortname='', url='', synctype='', branch='master', www_subdir="www", full='0'):
  # We need to iterate through the options in the map and find the right host based on
  # whether the repo name matches any of the options, as they may not be exactly identical

  # Try and read builder.ini from the home directory, if present
  print "===> Trying to read /home/vagrant/builder.ini if it is present"
  if os.path.isfile('/home/vagrant/builder.ini'):
    config.read('/home/vagrant/builder.ini')
    if config.has_section(shortname):
      env.host = config.get(shortname, 'hostname')
      env.user = config.get(shortname, 'username')
  else:
    # Let's ask the user rather than abort on a missing project in the builder.ini
    env.host  = prompt("We couldn't find the remote server in the builder.ini. What's the remote server or IP address to sync from?", default="dev1.example.com")
    env.user = prompt("What's your username on the remote server?", default="jenkins")

    config.add_section(shortname)
    config.set(shortname, 'hostname', env.host)
    config.set(shortname, 'username', env.user)
    print "Writing this configuration to to /home/vagrant/builder.ini"
    with open('/home/vagrant/builder.ini', 'ab') as configfile:
      config.write(configfile)

  env.host_string = '%s@%s' % (env.user, env.host)
  drush_cmd = '/usr/bin/drush'

  print "===> Host is %s" % env.host
  print "===> User is %s" % env.user
  print "===> Drush command is %s" % drush_cmd

  if synctype == "db":
    get_database(drush_cmd, shortname, branch)
  if synctype == "files": 
    get_files(drush_cmd, shortname, url, branch, www_subdir, full)
  if synctype == "all":
    get_database(drush_cmd, shortname, branch)
    get_files(drush_cmd, shortname, url, branch, www_subdir, full)
