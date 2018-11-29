import json

class RouteTable:
	def __init__(self):
		with open("routers_list.json", 'r') as file:
			self.routers_list = json.load(file)
		self.table = self.init_route_table(self.routers_list)
		
	#重置路由表
	def reset_table(self):
		self.table = self.init_route_table(self.routers_list)
	
	#初始化路由表
	def init_route_table(self, routers_list):
		table = {}
		for router in routers_list:
			table[tuple(router)] = self.init_each_row(routers_list) #routers_list是一个列表
			table[tuple(router)][tuple(router)] = {'cost':0, 'next_hop':tuple(router)}
		return table

	#初始化路由表的每一行
	def init_each_row(self, routers_list):
		destination = {}
		for router in routers_list:
			destination[tuple(router)] = {'cost':float("inf"), 'next_hop' : ()}
		return destination

	#更新路由表
	def update_table(self):
		for mid in self.routers_list:
			for sou in self.routers_list:
				for des in self.routers_list:
					if self.table[tuple(sou)][tuple(mid)]['cost'] + self.table[tuple(mid)][tuple(des)]['cost'] < self.table[tuple(sou)][tuple(des)]['cost']:
						self.table[tuple(sou)][tuple(des)]['cost'] = self.table[tuple(sou)][tuple(mid)]['cost'] + self.table[tuple(mid)][tuple(des)]['cost']
						self.table[tuple(sou)][tuple(des)]['next_hop'] = tuple(mid)

		



