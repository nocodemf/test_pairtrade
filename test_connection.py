from ib_insync import IB

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)
print("Connection successful!")
ib.disconnect()
