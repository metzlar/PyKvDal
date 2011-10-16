"""
PyKvDal
=======

Simple pure python Key Value Data Abstraction Layer.
See setup.py for more information on license and the author.
See README.rst and tests.py for information on usage.
"""
import uuid
import urllib
import json
import logging

store = None
logger = logging.getLogger(__name__)

try:
    from contracts import parse, ContractNotRespected
except ImportError:
    logger.warn((
            "Validation can not be used since PyContracts"
            "can not be imported"))


class IndexResult(list):
    """
    Represents a result from a queried index.

    IndexResult is lazy.
    IndexResult instances can be iterated and will only fetch the actual
    result from the store when the item is retrieved.

    Usage::

        >>> indexr = myModel.get_by_name("john")
        >>> indexr[0]  # <- Fetches the first result from the store
        >>> for res in indexr:  # <- Fetches all results one by one
        >>>     res.name
        <<< "john"
        <<< "john"
        <<< .. etc
    """

    def __init__(self, id_list, cls):
        super(IndexResult, self).__init__(id_list)
        self.cls = cls
        self.idx = 0

    def __iter__(self):
        return self

    def __getitem__(self, i):
        id = super(IndexResult, self).__getitem__(i)
        return self.cls.load(id)

    def next(self):
        try:
            result = self.cls.load(self.id_list[self.idx])
            self.idx += 1
            return result
        except IndexError:
            self.idx = 0
            raise StopIteration


class Field(object):
    """
    Base class for all fields.

    Usage::

        class MyModel(Model):
            '''Example model class'''

            field1 = Field("field1")
            field2 = Field("field2", default=5)

        >>> foo = MyModel()
        >>> foo.field2
        <<< 5
        >>> foo.field1 = 'bar'

    PyContracts can be used to specify a contract for the field's
    value. For example::

        field1 = Field("field1", contract="str")

    only validates values of type <str>. For more info check out
    http://pypi.python.org/pypi/PyContracts
    """

    def __init__(self, name, default=None, contract=None):
        self.name = name
        self.value = default
        self.contract = parse(contract) if contract else None

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if hasattr(instance,'__fld_' + self.name):
            return getattr(instance, '__fld_' + self.name)
        return self.value

    def __set__(self, instance, value):
        if self.name is None:
            raise AttributeError, "must define a name!"
        self.validate(value)
        setattr(instance, '__fld_' + self.name, value)

    def validate(self,value):
        """
        Validates this field instance's value. All fields are automatically
        validated right before the Model instance is saved to the store.
        An Exception is raised when the contract is not respected.
        """
        if self.contract:
            try:
                self.contract.check(value)
            except ContractNotRespected as cnr:
                raise Exception("Invalid value for "+self.name+": "+cnr.error)


class Index(object):
    """
    Represents an index of a Model.

    Usage::

        class MyModel(Model):
           name = Field("name")
           age = Field("age")

           get_by_name = Index("name")
           get_by_name_and_age = Index("name", "age")

        >>> foo = MyModel()
        >>> foo.name = "foo"
        >>> foo.age = 5
        >>> foo.save()
        >>> bar = MyModel()
        >>> bar.name = "bar"
        >>> bar.age = 5
        >>> bar.save()
        >>> for res in MyModel.get_by_name("foo"):
        >>>     print res

        <<< <MyModel name="foo", age=5>

        >>> for res in MyModel.get_by_age(5):
        >>>     print res

        <<< <MyModel name="foo", age=5>
        <<< <MyModel name="bar", age=5>
    """
    def __init__(self, *args):
        self.cols = args
        self.name = None
        self.owner = None

    def __get__(self, instance, owner):
        if not owner:
            owner = instance.__class__
        self.owner = owner
        return self

    def __call__(self, **kwargs):
        kwargs.update({'__index':self})
        return self.owner._query(**kwargs)


class Model(object):
    """Base class for all models."""

    indexes=None
    '''indexes set for this model'''

    def validate(self):
        for prop in self.__class__.__dict__.keys():
            class_attr = getattr(self.__class__, prop)
            if isinstance(class_attr, Field):
                value = getattr(self, prop, None)
                class_attr.validate(value)

    def __eq__(self, other):
        if hasattr(other, 'id'):
            return self.id == other.id
        return super(Model,self) == other

    def __init__(self):
        """Constructor creates a unique ID for each instance of a subclass."""
        self.id = uuid.uuid4().hex

    def save(self):
        """Store this instance."""
        if not hasattr(self,"id"):
            self.id = uuid.uuid4().hex
        self.validate()
        key = self.__class__.get_key_prefix()+ "#"+str(self.id)
        jsoned = dal_store(self)
        dal_set(key, jsoned)
        logger.debug( "SAVE %s %s ", str(key), str(jsoned))

        for index in self.__class__.get_indexes():
            key = "_".join([str(getattr(self, e)) for e in index.cols])
            key = index.name+"#"+key

            query_list = dal_get(key) or '[]'
            query_list = dal_retrieve(query_list)

            if type(query_list)!=type([]):
                query_list = [query_list]

            if not self.id in query_list:
                query_list.append(self.id)

            dal_set(
                key,
                dal_store(query_list))

    @classmethod
    def _from_dict(cls, dict_):
            result = cls()
            for k,v in dict_.iteritems():
                setattr(result,k,v)
            return result

    def _to_dict(self):
        dict_ = {}
        for k,v in self.__dict__.iteritems():
            if (k.startswith('__fld_')) or (not k.startswith('_')):
                dict_[k] = v
        return dict_

    @classmethod
    def get_key_prefix(cls):
        return "" + str(cls)

    def delete(self):
        """Removes this instance from the data layer."""
        if not hasattr(self, "id"):
            return
        key = self.__class__.get_key_prefix()+"#"+str(id)
        dal_delete(key)
        logger.debug( "DELE %s", str(key) )

        for index in self.__class__.get_indexes():
            key = "_".join([str(getattr(self, e)) for e in index.cols])
            key = index.name+"#"+key

            logger.debug( "DELE %s", str(key) )

            query_list = dal_get(key) or '[]'
            query_list = dal_retrieve(query_list)

            if type(query_list)!=type([]):
                query_list = [query_list]

            if self.id in query_list:
                query_list.remove(self.id)

            dal_set(
                key,
                dal_store(query_list))

    @classmethod
    def load(cls, id):
        """Load an instance from the data layer."""
        key = cls.get_key_prefix()+"#"+str(id)
        src = dal_get(key)
        logger.debug( "LOAD %s %s %s", str(key), str(id), str(src))
        if src == None:
            raise cls.NotExist("No instance could be found with ID: "+str(id))
        result = dal_retrieve(src)
        result = cls._from_dict(result)
        return result

    @classmethod
    def _query(cls, **kwargs):

        if not '__index' in kwargs:
            raise Exception("__index must be defined, current indexes: "+repr(
                    cls.get_indexes()))

        index = kwargs['__index']
        del kwargs['__index']
        key = index.name
        key = key + "#" + "_".join([str(kwargs[k]) for k in index.cols])
        src = dal_get(key)
        logger.debug( "QUERY %s %s", str(key), str(src))
        if src == None:
            return []

        result = dal_retrieve(src)
        if type(result) != type([]):
            result = [result]

        return IndexResult(result, cls)

    @classmethod
    def get_indexes(cls):
        """Retrieves all the 'with_query' methods of this class and
        returns tuples per function of the indexed property names"""
        if cls.indexes:
            return cls.indexes
        indexes = []

        for name in cls.__dict__.keys():
            value = getattr(cls, name)
            if isinstance(value, Index):
                indexes.append(value)
                value.name = cls.__name__ + '#' + name

        cls.indexes = indexes
        return cls.indexes


class NotExist(Exception):
    pass

Model.NotExist = NotExist

def dal_connect(connection_string):
    """
    """
    global store
    import memcache  # only if this method is used
    store = memcache.Client(connection_string)

def dal_set(key, obj):
    """
    Stores the given object under the given key into the data layer.
    By default this method utilizes the memcache.Client at ``pykvdal.store``.
    Repurpose this method to use a different data layer.

    For example::

        def mysql_set(key, obj):
            global conn
            conn.execute("INSERT INTO kv (key, value) VALUES (?,?)",
                urllib.quote(key),
                json.dumps(obj))

        pykvdal.dal_set = mysql_set
    """
    global store
    return store.set(urllib.quote(key), obj)

def dal_get(key):
    """
    Retrieves the object from the data layer with the given key.
    Returns None if the object is not found.
    By default this method utilizes the memcache.Client at ``pykvdal.store``.
    Repurpose this method to use a different data layer.

    For example::

        def mysql_get(key):
            global conn
            res = conn.execute("SELECT FROM kv WHERE key=?)",
                urllib.quote(key))
            return json.loads(res.scalar())

        pykvdal.dal_get = mysql_get
    """
    global store
    return store.get(urllib.quote(key))

def dal_delete(key):
    """
    Deletes the object from the data layer with the given key.
    By default this method utilizes the memcache.Client at ``pykvdal.store``.
    Repurpose this method to use a different data layer.

    For example::

        def mysql_delete(key):
            global conn
            conn.execute("DELETE FROM kv WHERE key=?)",
                urllib.quote(key))

        pykvdal.dal_delete = mysql_delete
    """
    global store
    return store.delete(urllib.quote(key))

def dal_retrieve(src):
    return json.loads(src)

def dal_store(obj):
    if hasattr(obj, '_to_dict'):
        obj = obj._to_dict()
    return json.dumps(obj)
