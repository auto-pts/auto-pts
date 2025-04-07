#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2018, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#

import datetime
import logging
import mimetypes
import os
import sys

from googleapiclient import discovery, errors
from googleapiclient.http import MediaFileUpload
from httplib2 import Http
from oauth2client import client, file, tools


SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'

log = logging.debug


class GDrive:
    def __init__(self, cfg):
        self.basedir_id = cfg['root_directory_id']
        self.cwd_id = self.basedir_id
        credentials = cfg['credentials_file']

        store = file.Storage(credentials)
        creds = store.get()
        if not creds or creds.invalid:
            path_abs = os.path.abspath(credentials)
            path = os.path.dirname(path_abs)

            flow = client.flow_from_clientsecrets(
                os.path.join(path, CLIENT_SECRET_FILE), SCOPES)
            creds = tools.run_flow(flow, store)
        self.service = discovery.build('drive', 'v3',
                                       http=creds.authorize(Http()))

    def pwd(self):
        return self.cwd_id

    def mkdir(self, name):
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [self.pwd()]
        }

        try:
            f = self.service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink').execute()
        except errors.HttpError:
            sys.exit(1)

        return f

    def ls(self):
        results = {}

        page_token = None
        while True:
            try:
                response = self.service.files().list(
                    q="'{}' in parents".format(self.pwd()),
                    spaces='drive',
                    fields='nextPageToken, files(id, name)',
                    pageToken=page_token).execute()
            except errors.HttpError:
                sys.exit(1)

            for f in response.get('files', []):
                results[f.get('name')] = f
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        return results

    def cp(self, name):
        if not os.path.exists(name):
            print("File not found")
            sys.exit(1)

        basename = os.path.basename(name)
        mime_type, encoding = mimetypes.guess_type(basename)

        file_metadata = {
            'name': basename,
            'parents': [self.pwd()]
        }

        media = MediaFileUpload(
            name,
            mimetype=mime_type)

        try:
            f = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name').execute()
        except errors.HttpError as err:
            print(err)
            sys.exit(1)

        return f

    def cd(self, dir_=None):
        """
            :param dir_: file object or id of the folder
        """
        if not dir_:
            self.cwd_id = self.basedir_id
        elif isinstance(dir_, str):
            self.cwd_id = dir_
        else:
            self.cwd_id = dir_.get('id')


class Drive(GDrive):
    def __init__(self, cfg):
        GDrive.__init__(self, cfg)
        self.url = None

    def new_workdir(self, iut):
        files = self.ls()
        if iut in list(files.keys()):
            dir_ = files[iut]
        else:
            dir_ = self.mkdir(iut)
        self.cd(dir_)
        dir_ = self.mkdir(datetime.datetime.now().strftime("%Y_%m_%d_%H_%M"))
        self.cd(dir_)
        return "{}".format(dir_.get('webViewLink'))

    def upload(self, f):
        print("Uploading {} ...".format(f))
        self.cp(f)
        print("Done")

    def upload_folder(self, folder, excluded=None):
        def recursive(directory):
            for f in os.scandir(directory):
                if excluded and (f.name in excluded or
                                 os.path.splitext(f.name)[1] in excluded):
                    continue

                if f.is_dir():
                    parent = self.pwd()
                    dir_ = self.mkdir(f.name)
                    self.cd(dir_)
                    recursive(os.path.join(directory, f.name))
                    self.cd(parent)
                else:
                    filepath = os.path.relpath(os.path.join(directory, f.name))
                    self.upload(filepath)

        recursive(folder)
