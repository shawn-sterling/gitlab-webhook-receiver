#!/usr/bin/python -tt
#
# Copyright (C) 2012 Shawn Sterling <shawn@systemtemplar.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# gitlab-webhook-receiver: a script for gitlab & puppet integration
#
# The latest version of this code will be found on my github page:
# https://github.com/shawn-sterling/gitlab-webhook-receiver

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import logging.handlers
import os
import re
import shutil
import subprocess


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

# this is the git ssh
git_ssh = "git@github.com"

log_max_size = 25165824         # 24 MB
log_level = logging.INFO
#log_level = logging.DEBUG      # DEBUG is quite verbose

##### You should stop changing things unless you know what you are doing #####
##############################################################################

log = logging.getLogger('log')
log.setLevel(log_level)
log_handler = logging.handlers.RotatingFileHandler(log_file,
                                                   maxBytes=log_max_size,
                                                   backupCount=4)
f = logging.Formatter("%(asctime)s %(filename)s %(levelname)s %(message)s",
                      "%B %d %H:%M:%S")
log_handler.setFormatter(f)
log.addHandler(log_handler)


class webhookReceiver(BaseHTTPRequestHandler):

    def run_it(self, cmd):
        """
            runs a command
        """
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        log.debug('running:%s' % cmd)
        p.wait()
        if p.returncode != 0:
            log.critical("Non zero exit code:%s executing: %s" % (p.returncode,
                                                                  cmd))
        return p.stdout

    def git_cleanup(self):
        """
            cleans up the master, does a prune origin
        """
        log.debug('git_cleanup begins')
        os.chdir(git_master_dir)
        cmd = "git reset --hard HEAD"
        self.run_it(cmd)
        cmd = "git pull"
        self.run_it(cmd)
        cmd = "git remote prune origin"
        self.run_it(cmd)
        log.debug('git_cleanup ends')

    def git_handle_branches(self):
        """
            gets a list of branches, does a reset then pull for each branch.
            clones any non existing branches.
        """
        log.debug('git_handle_branches begins')
        current_branches = ["master"]
        cmd = "git branch -a"
        output = self.run_it(cmd)
        for branch in output:
            branch = re.sub("\*", "", branch)
            branch = re.sub("\s+", "", branch)
            if not re.search("HEAD", branch):
                if not re.search("master", branch):
                    if re.search("/", branch):
                        short_name = branch.split('/')[2]
                        current_branches.append(short_name)
                        fwd = os.path.join(git_dir, short_name)
                        if os.path.isdir(fwd):
                            os.chdir(fwd)
                            log.debug('cwd:%s' % fwd)
                            cmd = "git reset --hard HEAD"
                            output = self.run_it(cmd)
                            cmd = "git pull"
                            output = self.run_it(cmd)
                        else:
                            os.chdir(git_dir)
                            cmd = "git clone -b %s %s:%s %s" % (
                                short_name, git_ssh, git_project, short_name)
                            output = self.run_it(cmd)
        log.debug('git_handle_branches ends')
        return current_branches

    def git_remove_stale_branches(self, current_branches):
        """
            removes any directories that don't have a branch name (ignores
            production dir/symlink)
        """
        log.debug('remove stale branches begins')
        # remove stale directories (deleted branches)
        if len(current_branches) > 1:
            current_directories = os.listdir(git_dir)
            for branch in current_branches:
                current_directories.remove(branch)
            # a production symlink must exist for puppet, ignore this dir
            if "production" in current_directories: 
                current_directories.remove("production")
            if len(current_directories) > 0:
                for branch in current_directories:
                    fwd = os.path.join(git_dir, branch)
                    log.debug("trying to remove:%s" % fwd)
                    try:
                        shutil.rmtree(fwd)
                    except (IOError, OSError) as e:
                        log.critical('Exception:%s removing dir:%s' % (fwd, e))
        log.debug('remove stale branches ends')

    def do_POST(self):
        """
            receives post, handles it
        """
        log.debug('got post')
        text = json.load(self.rfile)
        text = json.dumps(text, indent=2)
        if git_project in text:
            log.debug('project is in text')
            self.git_cleanup()
            current_branches = self.git_handle_branches()
            self.git_remove_stale_branches(current_branches)
            log.debug('post complete')
        else:
            log.debug('project name not in text, ignoring post')


def main():
    """
        the main event.
    """
    try:
        server = HTTPServer(('', 8000), webhookReceiver)
        log.info('started web server...')
        server.serve_forever()
    except KeyboardInterrupt:
        log.info('ctrl-c pressed, shutting down.')
        server.socket.close()

if __name__ == '__main__':
    main()
