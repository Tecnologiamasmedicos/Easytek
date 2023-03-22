import pysftp
from urllib.parse import urlparse
import os


def connect(hostname, username, password, port):
    """Connects to the sftp server and returns the sftp connection object"""

    try:
        # Get the sftp connection object
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        connection = pysftp.Connection(
            host=hostname,
            username=username,
            password=password,
            port=port,
            cnopts=cnopts,
        )
        return connection
    except Exception as err:
        raise Exception(err)


def disconnect(connection):
    """Closes the sftp connection"""
    try:
        connection.close()
    except Exception as err:
        raise Exception(err)
    print(f"Disconnected from host")


def listdir(connection, remote_path):
    """lists all the files and directories in the specified path and returns them"""
    for obj in connection.listdir(remote_path):
        yield obj


def download(connection, remote_path, target_local_path):
    """
    Downloads the file from remote sftp server to local.
    Also, by default extracts the file to the specified target_local_path
    """

    try:

        # Create the target directory if it does not exist
        path, _ = os.path.split(target_local_path)
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except Exception as err:
                raise Exception(err)

        # Download from remote sftp server to local
        connection.get(remote_path, target_local_path)
        print("download completed")

    except Exception as err:
        raise Exception(err)
