import socket 
import json
import sys
from threading import Thread
import threading
from protocol import *
import struct
from centralRouter import *
from time import ctime
import os

def get_addr_settings():
	try:
		with open('settings.json', 'r') as settings:
			addr, port = json.load(settings)
	except:
		print("无法打开配置文件!")
	else:
		return (addr, port)


def build_socket():
	try:
		router_accept_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except Exception as e:
		print("创建服务套接字失败！")
		sys.exit()
	else:
		try:
			addr, port = get_addr_settings()
			router_accept_socket.bind((addr, port))
		except:
			print("绑定套接字失败！")
			router_accept_socket.close()
			sys.exit()
		else:
			router_accept_socket.listen(1000)
			return router_accept_socket


def deal_router_connection(centralRouter, connect_socket, addr):
	header = connect_socket.recv(HEADER_SIZE)
	sou_addr, des_addr, msg_type, size, seq, passby = struct.unpack(HEADER_FORM, header)
	sou_addr = tuple(json.loads(sou_addr.decode('utf-8').strip('\0')))
	des_addr = tuple(json.loads(des_addr.decode('utf-8').strip('\0')))
	centralRouter.print_date_and_name()
	if msg_type == Type.ONLINE:
		print("[%s:%s]上线了！"%sou_addr)
		centralRouter.routers_online(sou_addr)
		centralRouter.print_table()
	elif msg_type == Type.OFFLINE:
		print("[%s:%s]下线了！"%sou_addr)
		centralRouter.routers_offline(sou_addr)
		centralRouter.print_table()
	elif msg_type == Type.ASK:
		print("[%s:%s]询问下一跳路由！"%sou_addr)
		centralRouter.answer(connect_socket, sou_addr, des_addr)
	connect_socket.close()




def start_centralrouter():
	router_socket = build_socket()
	print("中心路由地址为%s,端口为%s"%router_socket.getsockname())
	centralRouter = CentralRouter(router_socket)
	while True:
		connect_socket, addr = router_socket.accept()
		deal_connection = Thread(target = deal_router_connection, args = (centralRouter, connect_socket, addr))
		deal_connection.start()

if __name__ == "__main__":
	start_centralrouter()