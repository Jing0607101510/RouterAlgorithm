import struct
import json

HEADER_FORM = '30s30sllll'
HEADER_SIZE = struct.calcsize(HEADER_FORM)

class Type:
	DATA = 0
	ONLINE = 1
	OFFLINE = 2
	ACK = 3
	


class Protocol:
	def __init__(self, sou_addr, des_addr, msg_type, size = 0, seq = 0, passby = 0):
		self.sou_addr = sou_addr
		self.des_addr = des_addr
		self.size = size
		self.msg_type = msg_type
		self.seq = seq
		self.passby = passby
	#按照协议格式，将数据打包成指定格式
	def make_header(self):
		sou_addr = json.dumps(self.sou_addr).encode('utf-8')
		des_addr = json.dumps(self.des_addr).encode('utf-8')
		header = struct.pack(HEADER_FORM, sou_addr, des_addr,
			self.msg_type, self.size, self.seq, self.passby)
		return header