Python Key Value Data Abstraction Layer
======================

PyKvDal lets you easily do object-to-key-value-database-abstraction.
It supports memcached out of the box but other backends can be used without much effort.

Getting started
---------------

PyKvDal connects to ``memcached`` by default::

  pykvdal.dal_connect(['127.0.0.1:11211'])

Or repurpose ``dal_set()``, ``dal_get()`` and ``dal_delete()`` to use other backends.
Any backend that can support key-value storing, retreiving and deletion is supported:
MySQL, PostgreSQL, memcached, mongodb, redis, couchdb ... and many more.

All models must subclass ``BaseModel``, that's all::

  class Person(pykvdal.Model):
    pass

Now you can do stuff like::

  p = Person()
  p.name = 'foo'
  p.age = 13
  p.save()  # stores it in the database, assigns p.id

Retreiving the saved instance::

  p_identical = Person.load(p.id)
  print p_identical.name  # >>> 'foo'

Simple querying is supported, first define an ``Index``::

  class Person(pykvdal.Model):
    get_by_age = pykvdal.Index('age')

Now to query the above created ``Person``::

  res = Person.get_by_age(13)
  for p in res:
    print p.name

Limited field validation is implemented using ``PyContracts``::

  class Person(pykvdal.Model):
    age = pykvdal.Field('age', default=0, contract='int')
    name = pykvdal.Field('name', contract='str')

Why use PyKvDal
---------------

Ever started a project when you didn't know what datastore to use? SQL or NOSQL?
PostgreSQL or Mongodb? The requirements were unclear, specially the non-functional
requirements so you chose MySQL since its reasonable fast and supports transactions?
PyKvDal makes you not worry about these things at the start of the project. There is
only one file and it is designed to be replaced by a proper ORM or document store mapper
when the type of database has been decided. PyKvDal just lets you begin without worries
while you know you can easily transfer to another solution or just connect PyKvDal to
the correct database.

Manual
------

TODO: Write proper manual. (For now check the source of pykvdal.py ;-)

Feature list
------------

- Popuplar backends implemented
- Proper subclasses for validated fields e.b. StringField, IntField, etc.
