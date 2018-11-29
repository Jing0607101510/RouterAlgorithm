from time import ctime
from protocol import *
import socket
CENTRALROUTER = ('127.0.0.1', 50004)


class Router():
	def __init__(self, router_socket, local_addr):
		self.local_addr = local_addr
		self.router_socket = router_socket
		self.online()

	#ok!!
	def find_next_hop(self, des_addr):
		protocol = Protocol(self.local_addr, des_addr, Type.ASK)
		header = protocol.make_header()
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(CENTRALROUTER)
		sock.sendall(header)
		ans = sock.recv(HEADER_SIZE)
		sou_addr, next_addr, msg_type, size, seq, passby = struct.unpack(HEADER_FORM, ans)
		next_addr = tuple(json.loads(next_addr.decode('utf-8').strip('\0')))
		sock.close()
		return (next_addr, seq)


	#ok!
	def forward_data(self, des_addr, msg):
		while True:
			try:
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect(des_addr)
			except Exception as e:
				print(e)
				break
			else:
				sock.sendall(msg)
				sock.close()
				break

	#ok!
	def send_msg(self):
		self.print_date_and_name()
		msg = input("请输入你想要发送的信息：")
		self.print_date_and_name()
		ip = input("请输入目标ip地址（格式为xxx.xxx.xxx.xxx）:")
		self.print_date_and_name()
		port = int(input("请输入目标端口（格式为xxxxx）："))
		des_addr = (ip, port)
		next_addr, cost = self.find_next_hop(des_addr)
		if next_addr != ('0.0.0.0', 0):
			msg = msg.encode('utf-8')
			data_size = len(msg)
			protocol = Protocol(self.local_addr, des_addr, Type.DATA, data_size)
			header = protocol.make_header()
			self.forward_data(next_addr, header+msg)
			print("从[%s : %s]"%self.local_addr, end='')
			print("到[%s : %s]"%des_addr, end='')
			print("花费为%s"%cost)
		else:
			self.print_date_and_name()
			print("目的地不能到达！")


	def online(self):
		self.print_date_and_name()
		print("正在向中心路由注册...")
		protocol = Protocol(self.local_addr, CENTRALROUTER, Type.ONLINE)
		header = protocol.make_header()#fooline时，sou_addr代表下线的路由
		self.forward_data(CENTRALROUTER, header)


	#
	def offline(self):
		protocol = Protocol(self.local_addr, CENTRALROUTER, Type.OFFLINE)
		header = protocol.make_header()#fooline时，sou_addr代表下线的路由
		self.forward_data(CENTRALROUTER, header)


	#ok!
	def print_date_and_name(self):
		print('[%s]'%ctime(), '[%s : %s]'%(self.local_addr), end=' : ')
