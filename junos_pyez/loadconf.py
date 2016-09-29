#!/usr/bin/python

# copied from: http://www.juniper.net/techpubs/en_US/junos-pyez1.0/topics/example/junos-pyez-program-configuration-data-loading-from-file.html
# Adapted with some additions for ITOps device config automation


from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *

host = 'HOST.DOMAIN'
user = 'USER'
passw = 'PASSWORD'

conf_file = 'loadfile.conf'

def main():
    dev = Device(host=host,user=user,password=passw)

    # open a connection with the device and start a NETCONF session
    try:
        dev.open()
    except Exception as err:
        print "Cannot connect to device:", err
        return

    dev.bind( cu=Config )
    dev.timeout = 10*60

    # Lock the configuration, load configuration changes, and commit
    print "Locking the configuration"
    try:
        dev.cu.lock()
    except LockError:
        print "Error: Unable to lock configuration"
        dev.close()
        return

    print "Loading configuration changes"
    try:
        #dev.cu.load(path=conf_file, merge=True) #<-- to merge config
        #dev.cu.load(path=conf_file, overwrite=True) #<-- to overwrite config
        dev.cu.load(path=conf_file) 		#<-- to replace config
    except ValueError as err:
        print err.message

    except Exception as err:
        if err.rsp.find('.//ok') is None:
            rpc_msg = err.rsp.findtext('.//error-message')
            print "Unable to load configuration changes: ", rpc_msg

        print "Unlocking the configuration"
        try:
                dev.cu.unlock()
        except UnlockError:
                print "Error: Unable to unlock configuration"
        dev.close()
        return

    print "Committing the configuration"
    try:
        dev.cu.commit()
    except CommitError:
        print "Error: Unable to commit configuration"
        print "Unlocking the configuration"
        try:
            dev.cu.unlock()
        except UnlockError:
            print "Error: Unable to unlock configuration"
        dev.close()
        return

    print "Unlocking the configuration"
    try:
         dev.cu.unlock()
    except UnlockError:
         print "Error: Unable to unlock configuration"


    # End the NETCONF session and close the connection
    dev.close()

if __name__ == "__main__":
        main()
