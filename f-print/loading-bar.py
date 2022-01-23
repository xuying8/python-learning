#coding: utf-8
import time 
print("下载进度条loading ")
for i in range (20):
	print('.',end='',flush=True)
	time.sleep(0.75)
print("\n 下载成功")
