import socket
import json
from protocol import *
from time import ctime

class RouteTable:
	def __init__(self, local_addr, neighbours):
		self.table = self.init_route_table(neighbours)
		with open("routers_list.json", 'r') as file:
			self.routers_list = json.load(file)
		self.own_table = self.init_own_row(local_addr, self.routers_list, neighbours)
		
		

	#初始化邻居的路由表	
	def init_route_table(self, neighbours):
		with open("routers_list.json", 'r') as file:
			routers_list = json.load(file)

		table = {}
		for neighbour in neighbours:
			table[tuple(neighbour[0])] = self.init_each_row(routers_list) #routers_list是一个列表
		return table

	#初始化自己的路由表
	def init_own_row(self, local_addr, routers_list, neighbours):
		destination = self.init_each_row(routers_list)
		#for neighbour in neighbours:
		#	destination[tuple(neighbour[0])] = {'cost' : neighbour[1], 'next_hop' : tuple(neighbour[0])}
		destination[local_addr] = {'cost' : 0, 'next_hop' : local_addr}
		return destination

	#初始化邻居的路由表的每一行
	def init_each_row(self, routers_list):
		destination = {}
		for router in routers_list:
			destination[tuple(router)] = {'cost':float("inf"), 'next_hop' : ()}
		return destination

	#更新路由表
	def update_table(self, neighbours, local_addr, neighbour_addr, table, routers_list):
		has_change = 0
		cost = float('inf')
		for neighbour in neighbours:
			if tuple(neighbour[0]) == neighbour_addr:
				cost = neighbour[1]
		if self.own_table[neighbour_addr]['cost'] == float('inf'):
			self.own_table[neighbour_addr]['cost'] = cost
			self.own_table[neighbour_addr]['next_hop'] = neighbour_addr
			has_change = 1
		table = json.loads(table)
		neighbour_table = {}
		for key, value in table.items():
			key = key.replace("'", '\"')
			neighbour_table[tuple(json.loads(key))] = value
		self.table[neighbour_addr] = neighbour_table
		for router in routers_list:
			if self.own_table[tuple(router)]['cost'] >  self.own_table[neighbour_addr]['cost'] + neighbour_table[tuple(router)]['cost']:
				self.own_table[tuple(router)]['cost'] = self.own_table[neighbour_addr]['cost'] + neighbour_table[tuple(router)]['cost']
				self.own_table[tuple(router)]['next_hop'] = neighbour_addr
				print('[%s]'%ctime(), '[%s : %s]'%(local_addr), end=' : ')
				print("路由表有变化！")
				has_change = 1
		if has_change == 1:
			return True
		else:
			return False

	#重置路由表
	def reset_table(self, neighbours, local_addr):
		self.table = self.init_route_table(neighbours)
		self.own_table = self.init_own_row(local_addr, self.routers_list, neighbours)



#with open("neighbours.json", 'r') as file:
#	neighbours = json.load(file)
#	print(neighbours)

#test = RouteTable(('127.0.0.1', 49999), neighbours)
#for i, j in test.table.items():
#	print(i, j)


class Router():
	def __init__(self, router_socket, local_addr):
		with open('neighbours.json') as file:
			self.neighbours = json.load(file)
		self.local_addr = local_addr
		self.route_table = RouteTable(self.local_addr, self.neighbours)
		self.router_socket = router_socket
		with open("routers_list.json", 'r') as file:
			self.routers_list = json.load(file)
		self.seq = 0
		self.forward_table()

	#根据路由表找到吓一跳路由
	def find_next_hop(self, des_addr):
		next_hop = self.route_table.own_table[des_addr]['next_hop']
		return next_hop

	#向下一条路由转发数据
	def forward_table(self):
		table = {}
		for key, value in self.route_table.own_table.items():
			table[str(list(key))] = value
		own_table = json.dumps(table).encode('utf-8')
		table_size = len(own_table)
		has_change = 0
		for neighbour in self.neighbours:
			protocol = Protocol(self.local_addr, tuple(neighbour[0]), Type.TABLE, table_size, self.seq)
			header = protocol.make_header()
			while True:
				try:
					#self.print_date_and_name()
					#print("正在连接%s : %s"%tuple(neighbour[0]))
					sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					sock.connect(tuple(neighbour[0]))#还要定义协议
				except ConnectionRefusedError as e: 
					self.route_table.own_table[tuple(neighbour[0])]['cost'] = float('inf')
					self.route_table.own_table[tuple(neighbour[0])]['next_hop'] = ()
					self.print_date_and_name()
					#print("该路由器不在线上")
					break
				except Exception as e:
					print(e)
					continue
				else:
					if self.route_table.own_table[tuple(neighbour[0])]['cost'] == float('inf'):
						self.route_table.own_table[tuple(neighbour[0])]['cost'] = neighbour[1]
						self.route_table.own_table[tuple(neighbour[0])]['next_hop'] = tuple(neighbour[0])
						has_change = 1
					sock.sendall(header)
					sock.sendall(own_table)
					sock.close()
					break
		if has_change == 1:
			self.forward_table()

	#想下一跳路由转发数据
	def forward_data(self, des_addr, msg):
		while True:
			try:
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.connect(des_addr)
			except:
				break
			else:
				sock.sendall(msg)
				sock.close()
				break

	#向目的路由转发消息，首先发给下一跳路由
	def send_msg(self):
		self.print_date_and_name()
		msg = input("请输入你想要发送的信息：")
		self.print_date_and_name()
		ip = input("请输入目标ip地址（格式为xxx.xxx.xxx.xxx）:")
		self.print_date_and_name()
		port = int(input("请输入目标端口（格式为xxxxx）："))
		des_addr = (ip, port)
		if list(des_addr) in self.routers_list and self.route_table.own_table[des_addr]['cost'] != float('inf'):
			next_hop = self.find_next_hop(des_addr)
			msg = msg.encode('utf-8')
			data_size = len(msg)
			protocol = Protocol(self.local_addr, des_addr, Type.DATA, data_size)
			header = protocol.make_header()
			self.forward_data(next_hop, header+msg)
			self.print_date_and_name()
			print("总花费为%s"%self.route_table.own_table[des_addr]['cost'])
		else:
			self.print_date_and_name()
			print("目的地不能到达！")

	#打印路由表
	def print_table(self):
		self.print_date_and_name()
		print()
		for key, value in self.route_table.own_table.items():
			print("从本地路由[%s ： %s]"%self.local_addr,end="")
			print("到另一个路由[%s ： %s]"%key,end='')
			print("的最短路程为%s"%value['cost'], end='')
			if value['cost'] == float('inf'):
				print(",下一跳路由为----")
			else:
				print(",下一跳路由为[%s : %s]"%value['next_hop'])

	#向邻居报告下线消息
	def offline(self, offline_addr):
		self.seq += 1
		for neighbour in self.neighbours:
			protocol = Protocol(offline_addr, tuple(neighbour[0]), Type.OFFLINE, 0, self.seq)
			header = protocol.make_header()#fooline时，sou_addr代表下线的路由
			self.forward_data(tuple(neighbour[0]), header)

	#处理邻居发来的下线消息
	def deal_offline(self, addr, seq):
		self.print_date_and_name()
		print("重新设置路由表！")
		self.route_table.reset_table(self.neighbours, self.local_addr)
		self.offline(addr)
		self.forward_table()

	#打印时间和路由地址端口
	def print_date_and_name(self):
		print('[%s]'%ctime(), '[%s : %s]'%(self.local_addr), end=' : ')


