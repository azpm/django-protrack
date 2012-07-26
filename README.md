django-protrack
===============

Command Line loader for Protrack (informixDB) into a django managed db

Usage
=====

python manage.py load_protrack <channel_keyname>

prerequisites
=============

Protrack runs on top an informix installation, so you will need:

python-informix: http://informixdb.sourceforge.net

Setting up informix can be somewhat challenging, and beyond the scope of this project,
suffice it to say you will need a Linux host with a user _informix_ (group _informix_),
and the IBM Informix SDK. The SDK installer uses java and I've had the most success with
**jdk-6u32-linux-x64-rpm.bin** and not openjdk.

And, you will need:

sql-alchemy: http://www.sqlalchemy.org version 0.7.6 or better

This loader connects to informix using configuration provided by a django application,
chronologia, and loads information in.