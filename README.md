# Introduction

gitlab-webhook-receiver is a script to receive http posts from gitlab and then
pull the latest branches from a git repo.


# License

gitlab-webhook-receiver is released under the [GPL v2](http://www.gnu.org/licenses/gpl-2.0.html).


# Documentation

(1) Modify the script
---------------------

Modify the script near the top where it looks like this:
<pre>
############################################################
##### You will likely need to change some of the below #####

# log file for this script
log_file = '/var/lib/puppet/gitlab-webhook-receiver/webhook.log'

# where the puppet base git dir is
git_dir = "/etc/puppet/environments"

# the puppet master environment
git_master_dir = "/etc/puppet/environments/master"

# this is the name of the gitlab project name
git_project = "newpuppet"

# this is the git ssh account
git_ssh = "git@github.com"

log_max_size = 25165824         # 24 MB
log_level = logging.INFO
#log_level = logging.DEBUG      # DEBUG is quite verbose

##### You should stop changing things unless you know what you are doing #####
##############################################################################
</pre>

update it with where your dirs live.


(2) create the gitlab webhook
-----------------------------

In gitlab, as admin, go to "Hooks" tab, create hook as:
http://your.ip.goes.here:8000

or change the port on line 175 of the script.


(3) Optional init script
------------------------

Remember to edit the script if any of your directories were changed.


(4) Do initial checkout manually
--------------------------------
Whatever your git_dir is, do the first checkout manually. The script is made
to work with a pre-existing setup; and this gives you a chance to make sure
your permissions/ssh keys are all setup properly. 


# Trouble getting it working?

Let me know what's happening and I'll try to help. Email me at
shawn@systemtemplar.org.


# Contributing

I'm open to any feedback / patches / suggestions.

Shawn Sterling shawn@systemtemplar.org
