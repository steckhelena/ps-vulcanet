from collections import OrderedDict, namedtuple
import readline
import cmd


class CallCenter():
    delimiter = "\n"
    OperatorState = namedtuple(
        "OperatorState", ["available", "ringing", "busy"])(0, 1, 2)

    def __init__(self, operators: [str]):
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


class InteractiveCmd(cmd.Cmd):
    prompt = ">>> "  # This is pretty

    def __init__(self):
        super().__init__()
        self.callCenter = CallCenter(["A", "B"])

    def do_call(self, arg):
        "call <id>\tmakes application receive a call whose id is <id >"
        print(self.callCenter.receiveCall(arg), end='')

    def do_answer(self, arg):
        "answer <id>\tmakes operator <id> answer a call being delivered to it."
        print(self.callCenter.answerCall(arg), end='')

    def do_reject(self, arg):
        "reject <id>\tmakes operator <id> reject a call being delivered to it."
        print(self.callCenter.rejectCall(arg), end='')

    def do_hangup(self, arg):
        "hangup <id>\tmakes call whose id is <id> be finished."
        print(self.callCenter.hangupCall(arg), end='')


def main():
    InteractiveCmd().cmdloop()


if __name__ == "__main__":
    main()
