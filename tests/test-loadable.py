import sqlite3
import unittest
import time
import os

EXT_PATH="./dist/debug/ulid0"


def connect(ext, path=":memory:"):
  db = sqlite3.connect(path)

  db.execute("create temp table base_functions as select name from pragma_function_list")
  db.execute("create temp table base_modules as select name from pragma_module_list")

  db.enable_load_extension(True)
  db.load_extension(ext)

  db.execute("create temp table loaded_functions as select name from pragma_function_list where name not in (select name from base_functions) order by name")
  db.execute("create temp table loaded_modules as select name from pragma_module_list where name not in (select name from base_modules) order by name")

  db.row_factory = sqlite3.Row
  return db


db = connect(EXT_PATH)

def explain_query_plan(sql):
  return db.execute("explain query plan " + sql).fetchone()["detail"]

def execute_all(cursor, sql, args=None):
  if args is None: args = []
  results = cursor.execute(sql, args).fetchall()
  return list(map(lambda x: dict(x), results))

FUNCTIONS = [
  'ulid',
  'ulid',
  'ulid_bytes',
  'ulid_bytes',
  'ulid_datetime',
  'ulid_debug',
  'ulid_version',
  'ulid_with_prefix',
  
  
]

MODULES = []

class TestUlid(unittest.TestCase):
  def test_funcs(self):
    funcs = list(map(lambda a: a[0], db.execute("select name from loaded_functions").fetchall()))
    self.assertEqual(funcs, FUNCTIONS)

  def test_modules(self):
    modules = list(map(lambda a: a[0], db.execute("select name from loaded_modules").fetchall()))
    self.assertEqual(modules, MODULES)

    
  def test_ulid_version(self):
    self.assertEqual(db.execute("select ulid_version()").fetchone()[0][0], "v")

  def test_ulid_debug(self):
    debug = db.execute("select ulid_debug()").fetchone()[0].split('\n')
    self.assertEqual(len(debug), 3)
  
  def test_ulid(self):
    ulid = lambda: db.execute("select ulid()").fetchone()[0]
    self.assertEqual(len(ulid()), 26)
    self.assertEqual(type(ulid()), str)
  
  def test_ulid_bytes(self):
    ulid_bytes = lambda: db.execute("select ulid_bytes()").fetchone()[0]
    self.assertEqual(len(ulid_bytes()), 16)
    self.assertEqual(type(ulid_bytes()), bytes)
  
  def test_ulid_with_prefix(self):
    ulid_with_prefix = lambda prefix: db.execute("select ulid_with_prefix(?)", [prefix]).fetchone()[0]
    self.assertEqual(len(ulid_with_prefix("abc")), 26+4)
  
  def test_ulid_datetime(self):
    ulid_datetime = lambda ulid: db.execute("select ulid_datetime(?)", [ulid]).fetchone()[0]
    self.assertEqual(ulid_datetime('01GMP2G8ZG6PMKWYVKS62TTA41'), 1671483106288)
    #self.assertEqual(ulid_datetime(b'0185d0c5362761312e0483e4c9e3ec5d'), 1671483106288)
    self.assertEqual(ulid_datetime(b'\x01\x85\xe5\xb1\xc5\xe9\xfb\xa7\xf5\xcfSJ\x13\xe4.\xa3'), 1674595911145)
  
  

class TestCoverage(unittest.TestCase):                                      
  def test_coverage(self):                                                      
    test_methods = [method for method in dir(TestUlid) if method.startswith('test_ulid')]
    funcs_with_tests = set([x.replace("test_", "") for x in test_methods])
    for func in FUNCTIONS:
      self.assertTrue(func in funcs_with_tests, f"{func} does not have cooresponding test in {funcs_with_tests}")

if __name__ == '__main__':
    unittest.main()