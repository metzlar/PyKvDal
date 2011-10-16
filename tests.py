import unittest
import os
from pykvdal import(
    Model, Field, Index, dal_connect)
import pykvdal
import random

class SimpleModel(Model):
    myproperty=Field('myproperty', default='whatever', contract="str")
    foo=Field('foo', default='foll', contract="str")
    bar=Field('bar', default='foo', contract="str")

    get_by_foo=Index('foo')

class ReferingModel(Model):
    simple_id=Field('simple_id', default='id', contract="str|None")
    fubar=Field('fubar', default='barfu', contract="str")

    get_by_simple=Index('simple_id')
    get_by_simple_and_fubar=Index('simple_id', 'fubar')


class ModelCase(unittest.TestCase):

    def setUp(self):
        print "Starting memcached in the background"
        os.system("memcached &")
        dal_connect(['127.0.0.1:11211'])
        self.instances = []
        for i in range(10):
            s = SimpleModel()
            s.myproperty="s"+str(i)
            s.foo=str(random.randint(0,10))+"AAAAA"
            s.save()
            self.instances.append(s)

        self.referer = ReferingModel()
        self.referer.save()

    def tearDown(self):
        for s in self.instances:
            s.delete()
        self.referer.delete()

    def test_dal(self):
        self.instances[0].myproperty = "asdfads"
        self.instances[0].foo = "foo"
        self.instances[0].bar = "bar"
        self.instances[0].save()

        q = SimpleModel.get_by_foo(foo="foo")

        assert len(q) == 1
        assert q[0].id == self.instances[0].id

        self.instances[1].foo="foo"
        self.instances[1].save()

        assert len(SimpleModel.get_by_foo(foo="foo"))==2

        self.instances[2].bar = "bar"
        self.instances[2].save()

        assert len(SimpleModel.get_by_foo(foo="foo"))==2

        for i in range(3,10):
            self.instances[i].foo="foo"
            self.instances[i].save()

        assert len(SimpleModel.get_by_foo(foo="foo"))==9

        self.referer.foo="foo"
        self.referer.save()

        assert len(SimpleModel.get_by_foo(foo="foo"))==9

        self.referer.fubar="a"
        self.referer.simple_id = self.instances[5].id
        self.referer.save()

        assert len(ReferingModel.get_by_simple(
                simple_id=self.instances[5].id)) == 1

        assert len(ReferingModel.get_by_simple(
                simple_id=self.instances[4].id)) == 0

        assert len(ReferingModel.get_by_simple_and_fubar(
                simple_id=self.instances[5].id,
                fubar="b")) == 0

        assert len(ReferingModel.get_by_simple_and_fubar(
                simple_id=self.instances[5].id,
                fubar="a")) == 1


def hash_get(key):
    return DalCase.store[key] if key in DalCase.store else None

def hash_set(key, obj):
    DalCase.store[key] = obj

def hash_delete(key):
    if key in DalCase.store:
        del DalCase.store[key]


class DalCase(unittest.TestCase):

    store = {}

    def setUp(self):
        self.original_dal_get = pykvdal.dal_get
        self.original_dal_set = pykvdal.dal_set
        self.original_dal_delete = pykvdal.dal_delete
        pykvdal.dal_get = hash_get
        pykvdal.dal_set = hash_set
        pykvdal.dal_delete = hash_delete

        self.instances = []

        for i in range(10):
            s = SimpleModel()
            s.foo = "foo" + str(i)
            s.save()
            self.instances.append(s)

    def tearDown(self):
        for i in range(10):
            self.instances[i].delete()

        pykvdal.dal_get = self.original_dal_get
        pykvdal.dal_set = self.original_dal_set
        pykvdal.dal_delete = self.original_dal_delete

    def test_dal(self):
        for i in range(10):
            assert SimpleModel.load(
                self.instances[i].id) == self.instances[i]
