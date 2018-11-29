from socket import *
import json
import sys
from threading import Thread
import threading
from protocol import *
import struct
from router import *
from time import ctime
import os

#从配置文件值获取ip和端口
def get_addr_settings():
	try:
		with open('settings.json', 'r') as settings:
			addr, port = json.load(settings)
	except:
		print("无法打开配置文件!")
	else:
		return (addr, port)

#建立套接字
def build_socket():
	try:
		router_accept_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except Exception as e:
		print(e)
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

#处理用户的输入
def deal_client_input(router):
	while True:
		router.print_date_and_name()
		cmd = input("请输入指令：1.查看路由表；2.发送消息;3.从网络中断开\n")
		if cmd == '1':
			router.print_table()
		elif cmd == '2':
			router.send_msg()
		elif cmd == '3':
			print("从网络中断开！")
			router.offline(router.local_addr)
			router.router_socket.listen(0)
			router.router_socket.close()
			os._exit(0)
		else:
			print("请重新输入！")

#处理其他路由器的连接
def deal_router_io(router, connect_socket, addr):
	header = connect_socket.recv(HEADER_SIZE)
	sou_addr, des_addr, msg_type, size, seq, passby = struct.unpack(HEADER_FORM, header)
	sou_addr = tuple(json.loads(sou_addr.decode('utf-8').strip('\0')))
	des_addr = tuple(json.loads(des_addr.decode('utf-8').strip('\0')))
	recv_size = 0
	msg = ''
	while recv_size != size:
		if size - recv_size > 1024:
			data = connect_socket.recv(1024)
		else:
			data = connect_socket.recv(size - recv_size)
		recv_size += len(data)
		msg += data.decode('utf-8')
	if tuple(des_addr) == router.local_addr:
		if msg_type == Type.TABLE and seq == router.seq:
			is_new = router.route_table.update_table(router.neighbours, router.local_addr, sou_addr, msg, router.routers_list)
			if is_new == True:
				router.forward_table()
		elif msg_type == Type.DATA:
			router.print_date_and_name()
			print("[%s : %s]"%(sou_addr) + "发来消息:", msg)
		elif msg_type == Type.OFFLINE and seq == router.seq + 1:
			lock = threading.Lock()
			lock.acquire()
			router.print_date_and_name()
			print("[%s : %s]"%sou_addr+"下线！")
			router.deal_offline(sou_addr, seq)
			lock.release()
	else:
		protocol = Protocol(sou_addr, des_addr, msg_type, size, seq, passby+1)
		header = protocol.make_header()
		next_hop = router.find_next_hop(des_addr)
		msg = msg.encode('utf-8')
		router.forward_data(next_hop, header+msg)
		router.print_date_and_name()
		print("从[%s : %s]"%(sou_addr) + "到[%s :%s]"%(des_addr)+"的信息。到这里经过了%s跳"%(passby+1))

#等待其他路由器的连接
def wait_for_connection(router):
	while True:
		connect_socket, addr = router.router_socket.accept()
		deal = Thread(target = deal_router_io, args = (router, connect_socket, addr))
		deal.start()

#运行路由器
def start_router():
	router_socket = build_socket()
	local_addr = router_socket.getsockname()
	print("本路由地址为%s,端口为%s"%local_addr)
	router = Router(router_socket, local_addr)
	router_client = Thread(target = deal_client_input, args = [router])
	router_client.start()
	router_server = Thread(target = wait_for_connection, args = [router])
	router_server.start()

if __name__ == "__main__":
	start_router()


