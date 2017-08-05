# QuizUp Cache Traces

## Trace data format
480 1GB pcap-ng files containing a packet capture for all tcp and udp data received by the host on port 11211.
The protocol is the standard memcached protocol. The data it self is a binary encoded Thrift object (see player.thrift).

Thrift parsing example:
```
def parse_thrift(binary):
  transp = TTransport.TBufferedTransport(t.TMemoryBuffer(binary))
  proto = TBinaryProtocol.TBinaryProtocol(transp)
  player = Player()
  player.read(proto)
  return player
```

Note: I've noticed a flaw in the packet capture. That is that some of the payloads are incomplete, in those cases standard thrift decoders fail when decoding the payload.

## About setup
We captured all incoming traffic on the memcached port for one of five cache nodes in the cluster. Sharding  was done deterministically by key so the trace should contain all cache operations on a subset of Quizup users.
