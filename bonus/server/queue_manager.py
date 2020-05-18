from collections import OrderedDict, namedtuple
import json

from twisted.internet.protocol import Factory
from twisted.protocols import basic
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor


class CallCenter():
    delimiter = "\n"
    OperatorState = namedtuple(
        "OperatorState", ["available", "ringing", "busy"])(0, 1, 2)

    def __init__(self, operators: [str], factory):
        # Stores each operator state
        self.operatorStates = OrderedDict.fromkeys(
            operators, self.OperatorState.available)

        # A little more memory used, for the convenience of O(1) search time in both ways
        # Stores a map from an Operator id(key), to a CallId(value)
        self.operatorCallIds = dict()
        # Stores a map from callId(key) to an Operator id(value)
        self.callIdsOperator = dict()

        # Stores call in queue(actually a hashmap, so we can easily remove items in O(1))
        # sadly python does not have an ordered set :(
        self.callQueue = OrderedDict()

        self.factory = factory

    # This implementation does not require any extra memory used
    def checkCallIdAnswered(self, callId, operator):
        if operator in self.operatorCallIds and \
                self.operatorCallIds[operator] == callId and \
                self.operatorStates[operator] == self.OperatorState.ringing:
            self.rejectCall(operator)
            msg = "Call {} ignored by operator {}{}".format(
                callId, operator, self.delimiter)
            for connection in self.factory.clients:
                connection.sendResponse(msg)

        return ""

    # This is O(n) unfortunatelly. There are better solutions using a LRU, but then the order
    # would differ from the test example.
    def getNextAvailableOperator(self):
        for operator in self.operatorStates:
            if self.operatorStates[operator] == self.OperatorState.available:
                return operator
        return None

    def deliverCallToOperators(self, callId: str, operator: str = None):
        if not operator:
            operator = self.getNextAvailableOperator()

        if not operator:
            return ""

        self.operatorCallIds[operator] = callId
        self.callIdsOperator[callId] = operator
        self.operatorStates[operator] = self.OperatorState.ringing

        reactor.callLater(10, self.checkCallIdAnswered, callId, operator)

        return "Call {} ringing for operator {}{}".format(callId, operator, self.delimiter)

    def receiveCall(self, callId: str):
        operator = self.getNextAvailableOperator()
        msg = "Call {} received{}".format(callId, self.delimiter)
        if operator:
            msg += self.deliverCallToOperators(callId, operator)
        else:
            self.callQueue[callId] = None
            msg += "Call {} waiting in queue{}".format(callId, self.delimiter)

        return msg

    def answerCall(self, operator: str):
        if operator in self.operatorCallIds:
            callId = self.operatorCallIds[operator]
            self.operatorStates[operator] = self.OperatorState.busy
            return "Call {} answered by operator {}{}".format(callId, operator, self.delimiter)

        return ""

    def rejectCall(self, operator: str):
        msg = ""
        if operator in self.operatorCallIds:
            callId = self.operatorCallIds[operator]

            # Removes link between operator and call
            del self.callIdsOperator[callId]
            del self.operatorCallIds[operator]
            self.operatorStates[operator] = self.OperatorState.available

            # Moves call back to the beggining of the call queue
            self.callQueue[callId] = None
            self.callQueue.move_to_end(callId, last=False)

            msg += "Call {} rejected by operator {}{}".format(
                callId, operator, self.delimiter)
            msg += self.processCallQueue()

        return msg

    def hangupCall(self, callId: str):
        msg = ""
        if callId in self.callIdsOperator:
            operator = self.callIdsOperator[callId]
            del self.operatorCallIds[operator]
            del self.callIdsOperator[callId]

            if self.operatorStates[operator] == self.OperatorState.ringing:
                msg += "Call {} missed{}".format(callId, self.delimiter)
            else:
                msg += "Call {} finished and operator {} available{}".format(callId, operator,
                                                                             self.delimiter)
            self.operatorStates[operator] = self.OperatorState.available
            msg += self.processCallQueue()
        elif callId in self.callQueue:
            del self.callQueue[callId]
            msg += "Call {} missed{}".format(callId, self.delimiter)

        return msg

    def processCallQueue(self):
        if not self.callQueue.keys():
            return ""

        callId = self.callQueue.popitem(last=False)[0]
        return self.deliverCallToOperators(callId)


class CallCenterProtocol(basic.LineReceiver):
    delimiter = b'\n'

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.clients.add(self)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)

    def lineReceived(self, line):
        request = json.loads(line)

        if 'command' not in request:
            return

        response = ''
        if request['command'] == 'call':
            response = self.factory.call_center.receiveCall(request['id'])
        if request['command'] == 'answer':
            response = self.factory.call_center.answerCall(request['id'])
        if request['command'] == 'reject':
            response = self.factory.call_center.rejectCall(request['id'])
        if request['command'] == 'hangup':
            response = self.factory.call_center.hangupCall(request['id'])

        self.sendResponse(response)

    def sendResponse(self, msg):
        self.sendLine(json.dumps({'response': msg}).encode('ascii'))


class CallCenterFactory(Factory):
    protocol = CallCenterProtocol

    def __init__(self, operators: [str]):
        self.operators = operators
        self.call_center = None
        self.clients = set()

    def startFactory(self):
        self.call_center = CallCenter(self.operators, self)

    def buildProtocol(self, addr):
        return CallCenterProtocol(self)


def main():
    endpoint = TCP4ServerEndpoint(reactor, 5678)
    endpoint.listen(CallCenterFactory(['A', 'B']))
    reactor.run()


if __name__ == '__main__':
    main()
