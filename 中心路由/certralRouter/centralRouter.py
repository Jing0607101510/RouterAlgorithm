import routeTable
import json
from time import ctime
from protocol import *

class CentralRouter():
	def __init__(self, router_socket):
		with open('routers_list.json', 'r') as file:
			self.routers_list = json.load(file)
		self.online_routers = []
		self.route_table = routeTable.RouteTable()
		self.router_socket = router_socket
		self.local_addr = router_socket.getsockname()

	def routers_online(self, addr):
		self.set_cost(addr)
		self.online_routers.append(addr)
		self.route_table.update_table()
		

	def set_cost(self, addr):
		with open('costs.json', 'r') as file:
			costs = json.load(file)
		for cost in costs:
			if (addr == tuple(cost[0]) and tuple(cost[1]) in self.online_routers) or (addr == tuple(cost[1]) and tuple(cost[0]) in self.online_routers):
				self.route_table.table[tuple(cost[0])][tuple(cost[1])]['cost'] = cost[2]
				self.route_table.table[tuple(cost[0])][tuple(cost[1])]['next_hop'] = tuple(cost[1])
				self.route_table.table[tuple(cost[1])][tuple(cost[0])]['cost'] = cost[2]
				self.route_table.table[tuple(cost[1])][tuple(cost[0])]['next_hop'] = tuple(cost[0])
		

	def routers_offline(self, addr):
		self.online_routers.remove(addr)
		self.route_table.reset_table()
		for router in self.online_routers:
			self.set_cost(router)
		self.route_table.update_table()


	def answer(self, connect_socket, sou_addr, des_addr):
		if des_addr not in self.online_routers:
			des_addr = ('0.0.0.0', 0)
		else:
			cost = self.route_table.table[sou_addr][des_addr]['cost']
			des_addr = self.route_table.table[sou_addr][des_addr]['next_hop']
		protocol = Protocol(sou_addr, des_addr, Type.ANS, seq = cost)
		header = protocol.make_header()
		connect_socket.sendall(header)

	def print_date_and_name(self):
		print('[%s]'%ctime(), '[%s : %s]'%(self.local_addr), end=' : ')

	def print_table(self):
		for router, value in self.route_table.table.items():
			print("从[%s : %s]"%router+"到")
			for des, info in value.items():
				print("[%s : %s]"%des, end='')
				print("的花费为%s, 下一跳路由为%s"%(info['cost'], info['next_hop']))
		print()





