import socket
import json
from protocol import *
from time import ctime

class RouteTable:
	def __init__(self, local_addr, neighbours):
		with open("routers_list.json", 'r') as file:
			self.routers_list = json.load(file)
		self.line_state = self.init_line_state(self.routers_list)
		self.next_hop_to_des = {}
		self.cost = {}
		self.update_next_hop(local_addr)
		
	#def reset_cost(routers_list):
	#	cost = {}
	#	for router in routers_list:
	#		cost[tuple(router)] = float('inf')
	#	return cost
	#	
	#初始化链路状态
	def init_line_state(self, routers_list):
		line_state = {}
		for router in routers_list:
			line_state[tuple(router)] = self.init_each_row(routers_list) #routers_list是一个列表
			line_state[tuple(router)][tuple(router)] = 0
		return line_state

	#初始化链路状态的每一行
	def init_each_row(self, routers_list):
		destination = {}
		for router in routers_list:
			destination[tuple(router)] = float('inf')
		return destination

	#def reset_next_hop(self, routers_list, local_addr):
	#	next_hop = {}
	#	for router in routers_list:
	#		next_hop[tuple(router)] = tuple(router)
	#	return next_hop

	#将以指定地址为起点或者终点的链路花费置为无穷
	def remove_from_line_state(self, addr):
		for sou, des in self.line_state.items():
			des[addr] = float('inf')
		for des, cost in self.line_state[addr].items():
			self.line_state[addr][des] = float('inf')

	##将以指定地址为起点或者终点的链路花费设置为costs.json文件中的指定大小
	def add_to_line_state(self, addr, online_routers):
		with open('costs.json', 'r') as file:
			costs = json.load(file)
		for cost in costs:
			if (addr == tuple(cost[0]) and tuple(cost[1]) in online_routers) or (addr == tuple(cost[1]) and tuple(cost[0]) in online_routers):
				self.line_state[tuple(cost[0])][tuple(cost[1])] = cost[2]
				self.line_state[tuple(cost[1])][tuple(cost[0])] = cost[2]
	#更新路由表
	def update_next_hop(self, local_addr):
		flag = {}
		for router in self.routers_list:
			self.cost[tuple(router)] = self.line_state[local_addr][tuple(router)] 
			self.next_hop_to_des[tuple(router)] = tuple(router)
			flag[tuple(router)] = 0
		temp = local_addr
		flag[local_addr] = 1
	 	
		for router in self.routers_list:
	 		mi = float('inf')
	 		for router in self.routers_list:
	 			if (self.cost[tuple(router)] < mi) and flag[tuple(router)] == 0:
	 				mi = self.cost[tuple(router)]
	 				temp = tuple(router)
	 		if temp == local_addr:
	 			return
	 		flag[temp] = 1
	 		for router in self.routers_list:
	 			if self.cost[tuple(router)] > self.cost[temp] + self.line_state[temp][tuple(router)] and flag[tuple(router)] == 0:
	 				self.cost[tuple(router)] = self.cost[temp] + self.line_state[temp][tuple(router)]
	 				self.next_hop_to_des[tuple(router)] = self.next_hop_to_des[temp]


		


		






		
		







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
		self.online_routers = [self.local_addr]
		self.broadcast_online(self.local_addr)


	#根据路由表找到吓一跳路由
	def find_next_hop(self, des_addr):
		next_hop = self.route_table.next_hop_to_des[des_addr]
		return next_hop

	#向下一条路由转发数据
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
		if list(des_addr) in self.routers_list and self.route_table.cost[des_addr] != float('inf'):
			next_hop = self.find_next_hop(des_addr)
			msg = msg.encode('utf-8')
			data_size = len(msg)
			protocol = Protocol(self.local_addr, des_addr, Type.DATA, data_size)
			header = protocol.make_header()
			self.forward_data(next_hop, header+msg)
			self.print_date_and_name()
			print("总花费为%s"%self.route_table.cost[des_addr])
		else:
			self.print_date_and_name()
			print("目的地不能到达！")

	#打印路由表
	def print_table(self):
		self.print_date_and_name()
		print("从本地路由[%s : %s]到其他路由的费用如下："%self.local_addr)
		for key, value in self.route_table.next_hop_to_des.items():
			print("到[%s : %s]"%key, end='')
			print("的下一跳为[%s : %s],"%value, end='')
			print("花费为%s"%self.route_table.cost[key])

	#处理邻居发来的下线消息
	def deal_offline(self, addr, seq):
		self.seq = seq
		self.online_routers.remove(addr)
		self.broadcast_offline(addr)
		self.route_table.remove_from_line_state(addr)
		self.route_table.update_next_hop(self.local_addr)

	#处理邻居发来的上线消息
	def deal_online(self, addr):
		self.online_routers.append(addr)
		self.broadcast_online(addr)
		self.route_table.add_to_line_state(addr, self.online_routers)
		self.route_table.update_next_hop(self.local_addr)
		protocol = Protocol(self.local_addr, addr, Type.ACK)
		header = protocol.make_header()
		next_hop = self.find_next_hop(addr)
		self.forward_data(next_hop, header)
	
	#处理邻居发来的确认上线消息
	def deal_ack(self, addr):
		self.online_routers.append(addr)
		self.route_table.add_to_line_state(addr, self.online_routers)
		self.route_table.update_next_hop(self.local_addr)

	#全网广播上线
	def broadcast_online(self, local_addr):
		for neighbour in self.neighbours:
			protocol = Protocol(local_addr, tuple(neighbour[0]), Type.ONLINE)
			header = protocol.make_header()
			self.forward_data(tuple(neighbour[0]), header)

	#全网广播下线
	def broadcast_offline(self, local_addr):
		for neighbour in self.neighbours:
			protocol = Protocol(local_addr, tuple(neighbour[0]), Type.OFFLINE, seq=self.seq)
			header = protocol.make_header()
			self.forward_data(tuple(neighbour[0]), header)

	#打印时间和路由地址端口
	def print_date_and_name(self):
		print('[%s]'%ctime(), '[%s : %s]'%(self.local_addr), end=' : ')


