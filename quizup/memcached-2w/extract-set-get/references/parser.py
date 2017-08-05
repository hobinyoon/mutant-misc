
import sys 
sys.path.append('gen-py')


from thrift import Thrift 
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from player.ttypes import Player 




def binary_to_player(binary):
    transp = TTransport.TBufferedTransport(TTransport.TMemoryBuffer(binary))
    proto = TBinaryProtocol.TBinaryProtocol(transp)
    player = Player()
    while True:
        try:
            player.read(proto)
            print(player)
        except:
            break 
    return player

if __name__=="__main__":
        p = Player()
        with open("traces/{}".format(sys.argv[1]), 'rb') as ifile:
                # print(ifile.read())
                p = binary_to_player(ifile.read())
                # print(p)
                # print(p.id)
