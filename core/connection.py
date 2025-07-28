import paramiko
from dotenv import load_dotenv
import os

class Connection:
    def __init__(self):
        load_dotenv()
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.IP = os.getenv('VPS_IP')
        self.USERNAME = os.getenv('VPS_USERNAME')
        self.KEY = os.getenv('PRIVATE_KEY')
        self.PASSPHRASE = os.getenv('PASSPHRASE')
        if not self.connect():
            print("Connection failed with parameters: ", self.IP, self.USERNAME, self.KEY, self.PASSPHRASE, sep="\n")
            exit()
        else:
            print("Connected to VPS")

    def connect(self):
        try:
            self.ssh.connect(hostname=self.IP, username=self.USERNAME, key_filename=self.KEY, passphrase=self.PASSPHRASE)
            return True
        except Exception as e:
            print(e)
            return False

    def close(self):
        try:
            self.ssh.close()
            return True
        except Exception as e:
            print(e)
            return False