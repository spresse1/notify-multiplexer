#! /usr/bin/env python3

class Message():
	"""A class which implements the creating and sending of notify-format messages"""
	from json import dumps, loads
	
	def __init__(self,raw=None):
		self.data={}
		if raw: #we're parsing in a message that came off the wire
			while len(raw)>0:
				i=0
				while i<len(raw) and raw[i]!=ord(':'):
					i+=1
				key=raw[:i]
				if key==b"\0":
					#last byte
					break
				elif key!=b'body':
					j=1
					while j<len(raw) and raw[j]!=ord("\0"):
						j+=1
					data=raw[i+1:j]
					self.data[key.decode('UTF-8')]=data #decoded on fetch
					raw=raw[j+1:]
				else:
					bodylength=int(self.get_data('body-length'))
					self.data['body']=raw[i+1:][:bodylength]
					raw=raw[i+1:][bodylength:]
				
	def escape(self,bytes):
		ba = bytearray(bytes)
		i=0
		while i< len(ba): #have to account for it growing
			if ba[i]==0:
				ba.insert(i+1,0)
				i+=1 #skip next
			i+=1
		return ba
		
	def unescape(self,bytes):
		ba=bytearray(bytes)
		i=0
		while i<len(ba): #this time it might shrink
			if ba[i]==0 and len(ba)>i+1 and ba[i+1]==0:
				ba.pop(i+1)
			i+=1
		return ba
		
		
	def set_data(self, key, value):
		if ':' in key or "\0" in key:
			raise ValueError("Key cannot contain ':' or the null byte")
		self.data[key]=self.escape(bytes(str(value),'UTF-8'))
	
	def set_body(self, body):
		self.set_data('body',body)
		self.set_data('body-length',len(self.data['body']))
		#print(len(self.data['body']))
	
	def get_data(self, key):
		if key in self.data:
			return self.unescape(self.data[key]).decode('UTF-8')
		else:
			raise KeyError("No such key")
	def clear_data(self,key):
		if (key in self.data.keys()):
			del self.data[key]
	
	def __bytes__(self):
		ret=bytearray()
		for key in self.data.keys():
			if (key != 'body' and key != 'body-length'):
				ret+=bytes(key,'UTF-8') + b":" + self.data[key] + b"\0"
		if ('body-length' in self.data and 'body' in self.data):
			ret += b'body-length:' + self.data['body-length'] + b"\0body:" + self.data['body']
		ret = b'length:' + self.escape(bytes(str(len(ret)),'UTF-8')) + b"\0" + ret
		return ret
	
	def __str__(self):
		return sub("\0", "\n", str(self.__bytes__()))

import unittest
	
class TestDataInsert(unittest.TestCase):
	def setUp(self):
		self.msg=Message()
	
	def test_insert_arbitrary(self):
		self.msg.set_data('one', 'one')
		self.msg.set_data('two', 2)
		self.msg.set_data('escape',"\0")
		self.assertEqual(self.msg.escape(bytes('one','UTF-8')), self.msg.data['one'])
	
	def test_set_body(self):
		self.msg.set_body("hello\0world")
		self.assertEqual(self.msg.escape(bytes("hello\0world",'UTF-8')),self.msg.data['body'])
		self.assertEqual(self.msg.escape(bytes('12','UTF-8')),self.msg.data['body-length'])
	
	def test_get_body(self):
		self.msg.set_body("Hello World")
		self.assertEqual("Hello World", self.msg.get_data('body'))

class TestConvert(unittest.TestCase):
	def setUp(self):
		self.msg=Message()
		self.msg.set_data('tag','testtag')
		self.msg.set_body("Hello World")
	
	def test_bytes(self):
		self.assertEqual(bytes(self.msg),
			b"length:43\0tag:testtag\0body-length:11\0body:Hello World\0")
	
	def test_msg(self):
		msg = Message(bytes("length:31\0body-length:11\0body:Hello World\0",'UTF-8'))
		print(msg.data)
		self.assertEqual(msg.get_data('body'), "Hello World")
	
if __name__=='__main__':
	""" unit test time!"""
	class testEscaping(unittest.TestCase):
		def test_both(self):
			b = bytearray(b'test\0str')
			msg=Message()
			self.assertEqual(b,msg.unescape(msg.escape(b)))
			self.assertNotEqual(b,msg.escape(b))
	unittest.main()
	
