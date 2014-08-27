What is builder?
----------------

builder is a collection of shell scripts which allow you to effectively do
'zero touch' deployment of fresh sites into your Vagrant dev environment.


It comes with 4 'tasks':

    builder install
  
    builder update
  
    builder sync
  
    builder destroy


'install' does what you'd expect: pulls down a git repo, either imports 
database dump or drush site-install, creates nginx vhost, drush alias, cron
etc.

'update' doesn't do much more than 'git pull' and a drush updatedb and maybe
a cache clear.

'sync' is the most interesting: it will sync database and/or files from a
remote site to your local dev, e.g the version from remote dev or stage env.

'destroy' completely tears down a site.


USAGE instructions
------------------

Here's the output of running 'builder' without any arguments

    vagrant@773209869508:~$ builder
    You didn't provide a task to run! Valid options are install, update, sync, destroy
    usage: /usr/local/bin/builder ARGUMENT OPTIONS

    This script builds a new site for local development.

    ARGUMENTS:
       install <site>
       update  <site>
       sync    <site>
       destroy <site>

    OPTIONS for INSTALL:
       -n	Mandatory. Short name of your site. e.g if your URL was example.dev.example.com, shortname would be 'example'
       -g	Mandatory. URL of the git repository to clone.
       -b	Optional. Branch of the git repository to checkout. Defaults to 'master'
       -p	Optional. Install profile name. This must be the 'machine' name of the profile, e.g 
            'my_profile', not 'My Profile'. Defaults to 'standard'.
       -h   This help message

    OPTIONS for UPDATE:
       -h   This help message

    OPTIONS for SYNC:
       -n   Mandatory. Short name of your site. e.g if your URL was example.dev.example.com, short name would be example
       -s   Optional. Sync type. Valid options are 'db', 'files' or 'all'. 'all' is the default.
       -b	Optional. Branch to sync from (assuming that there are multiple branches on the remote side. Defaults to 'master'
       -c   Optional. Clean (sanitise) the databases to remove or protect sensitive data.
       -f   Optional. Perform a 'full' file sync (even large files), instead of only files 100k or smaller.

    OPTIONS for DESTROY:
       -n   Mandatory. Short name of your site. e.g if your URL was example.dev.example.com, short name would be example



As you can see, lots of options! 


EXAMPLES
--------

So, to get started! Let's install a fresh site.

      builder install foobar.dev.example.com -n foobar -g git@github.com:mig5/foobar.git

Note the -n (shortname), -g (git repo), and that I had to provide a URL to the 'builder install' command.

I highly recommend you keep it in the format of <shortname>.dev.example.com, where *.dev.example.com
resolves to localhost (for Vagrant).

Once that install is complete, you'll find you can reach http://foobar.dev.example.com:8080. It will be a generic
Drupal fresh install at this point, probably (depending on what's in your repo!).


Now to sync down the staging database/files from a remote staging server:

      builder sync foobar.dev.example.com -n foobar

Answer the prompts: 

    Host = staging.example.com for host, 
    Username = same username you SSH in to staging.example.com as

You'll find it pulls down database and rsyncs the assets. Hard-refresh http://foobar.dev.example.com:8080 in
your browser and you should find you get a much more up-to-date looking version of the site, or at least, it 
should match the staging version pretty closely.



CAVEATS
-------

There are a very large number of assumptions here, based on working practices at several agencies I contract
to. There is a very good chance that builder *will not work* for you out of the box, due to these assumptions.

These assumptions currently include:

1. Full Drupal codebase is stored in the Git repo (no Drush Make support yet)
2. Codebase is usually in a 'www' subfolder (but should work without it, or auto-detect 'docroot' Acquia style)
3. Assumes you are running Nginx, MySQL etc in Vagrant (and that you are using Vagrant)
4. Assumes you have the file /etc/nginx/conf.d/drupal_common_config which contains Drupal-friendly Nginx config.
   I have not included this in this repo right now - you could look at https://github.com/perusio/drupal-with-nginx
5. Assumes you are happy storing the sites in /vagrant in your Vagrant VM
6. You need to install Fabric if you want to use 'builder sync' - either via Wheezy-Backports repo for Debian 
   Wheezy, or 'pip install fabric'.
7. Syncing probably requires your SSH public key to be accepted on the remote side
8. Makes some assumptions about Drush aliases on the remote side using the same 'shortname' convention as local
9. Probably many other assumptions I am forgetting right now. It's an old program only recently open-sourced.


There is a lot of work to do to unpick these assumptions / support other things such as Apache etc.
