# -*- coding: utf-8 -*-

import psutil
import os
import pwd

from datetime import datetime
from stat import S_IRGRP, S_IRUSR
from subprocess import check_output
from glob import glob


class Base(object):
    def __init__(self):
        self.green_color = '\33[32m'
        self.red_color = '\33[31m'
        self.yellow_color = '\33[33m'
        self.cyan_color = '\033[36m'
        self.no_color = '\033[0m'

        self.checkmark = u'\u2713'
        self.crossmark = u'\u2717'
        self.warnmark = u'\u26A0'
        self.mark = None

        self.ltopbord = self.cyan_color + u'┌'.encode('utf-8') + self.no_color
        self.lbtmbord = self.cyan_color + u'└'.encode('utf-8') + self.no_color
        self.mdlbord = self.cyan_color + u'─'.encode('utf-8') + self.no_color
        self.rtopbord = self.cyan_color + u'┐'.encode('utf-8') + self.no_color
        self.rbtmbord = self.cyan_color + u'┘'.encode('utf-8') + self.no_color
        self.sidebord = self.cyan_color + '│' + self.no_color

        self.decorate_mode = False
        self.logs = []

    def file_change_timestamp(self, file_path):
        return self.os_stat(file_path).st_mtime

    def file_name(self, file_path):
        return os.path.basename(file_path)

    def dir_tree(self, dir_path, file_ext=None):
        tree = []

        for root, dirs, files in os.walk(dir_path):
            tree.append(root)

            for filename in files:
                if file_ext is not None:
                    if filename.endswith(file_ext):
                        tree.append(os.path.join(root, filename))
                else:
                    tree.append(os.path.join(root, filename))

        tree.pop(0)

        return tree

    def files(self, wildcard_file_path):
        return [os.path.join(os.path.split(x)[0], os.path.split(x)[-1]) for x in glob(wildcard_file_path)]

    def pid(self, name):
        return check_output(['pidof', name]).split(' ')

    def all_pids(self):
        return psutil.pids()

    def ps_name(self, pid):
        return psutil.Process(int(pid)).name()

    def ps_path(self, pid):
        try:
            return psutil.Process(int(pid)).exe()
        except psutil.AccessDenied:
            return 'Permission Denied'

    def file_owner(self, file_path):
        uid = self.os_stat(file_path).st_uid

        return pwd.getpwuid(uid).pw_name

    def file_group(self, file_path):
        gid = self.os_stat(file_path).st_gid

        return pwd.getpwuid(gid).pw_name

    def ps_owner(self, pid):
        proc_path = '/proc/%d'
        uid = self.os_stat(proc_path % int(pid)).st_uid

        return pwd.getpwuid(uid).pw_name

    def check_ps_access(self):
        try:
            return self.all_pids()
        except psutil.AccessDenied:
            return []

    def current_user(self):
        return pwd.getpwuid(os.getuid())[0]

    def check_file(self, file_path):
        return os.path.exists(file_path)

    def check_file_read_perms(self, file_path):
        st = self.os_stat(file_path)

        return bool(st.st_mode & S_IRUSR)

    def read_file(self, file_path):
        with open(file_path, 'r') as f:
            return f.read().splitlines()

    def os_stat(self, path):
        return os.stat(path)

    def datetime_now(self):
        return datetime.now()

    def pretty_print(self, message, message_type=''):
        if type(message) is list:
            message = ' '.join(message)

        if message_type is 'error':
            self.mark = self.red_color + self.crossmark.encode('utf-8')
        elif message_type is 'warn':
            self.mark = self.yellow_color + self.warnmark.encode('utf-8')
        else:
            self.mark = self.green_color + self.checkmark.encode('utf-8')

        message = "{0} {1}{2}".format(self.mark, message, self.no_color)

        if self.decorate_mode:
            self.logs.append(message)
        else:
            print(message)

    def decorate(self):
        if self.decorate_mode:
            lines = ['check {0} - {1}'.format(i + 1, log) for i, log in enumerate(self.logs)]
            spchar_extra_width = len(self.mark + self.no_color) - 1
            width = max(len(line) for line in lines)

            log_list = [self.ltopbord + self.mdlbord * (width - spchar_extra_width) + self.rtopbord]

            for line in lines:
                log_list.append(self.sidebord + (line + ' ' * width)[:width] + self.sidebord)

            log_list.append(self.lbtmbord + self.mdlbord * (width - spchar_extra_width) + self.rbtmbord)

            print '\n'.join(log_list)

        print '\n'
