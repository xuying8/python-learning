#i want to build an off-chance tuple, with 15 words(abc,%^,etc).  
#so what first? 
#start with simple list knowledge
import random 
list=[]
for x in range (1,16):
	x=random.randint(0,9)
	list.append(x)
print(list)
