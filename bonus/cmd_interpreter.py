import readline
import cmd
import json

from twisted.internet import reactor
from twisted.protocols import basic
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol


class CallcenterQueueClient(basic.LineReceiver):
    delimiter = b'\n'

    def sendMessage(self, msg):
        self.sendLine("{}".format(msg).encode('ascii'))

    def lineReceived(self, line):
        response = json.loads(line)
        if 'response' in response:
            print(response['response'])


class InteractiveCmd(cmd.Cmd):
    prompt = ""  # This is pretty

    def __init__(self):
        super().__init__()
        self.got_protocol = False
        self.protocol = None

    def gotProtocol(self, protocol):
        self.protocol = protocol
        self.got_protocol = True

    def do_echo(self, arg):
        print(arg)

    def do_call(self, arg):
        "call <id>\tmakes application receive a call whose id is <id >"
        if not self.got_protocol:
            return

        reactor.callFromThread(self.protocol.sendMessage,
                               json.dumps({'command': 'call', 'id': arg}))

    def do_answer(self, arg):
        "answer <id>\tmakes operator <id> answer a call being delivered to it."
        if not self.got_protocol:
            return

        reactor.callFromThread(self.protocol.sendMessage,
                               json.dumps({'command': 'answer', 'id': arg}))

    def do_reject(self, arg):
        "reject <id>\tmakes operator <id> reject a call being delivered to it."
        if not self.got_protocol:
            return

        reactor.callFromThread(self.protocol.sendMessage,
                               json.dumps({'command': 'reject', 'id': arg}))

    def do_hangup(self, arg):
        "hangup <id>\tmakes call whose id is <id> be finished."
        if not self.got_protocol:
            return

        reactor.callFromThread(self.protocol.sendMessage,
                               json.dumps({'command': 'hangup', 'id': arg}))

    def do_exit(self, _):
        reactor.callFromThread(reactor.stop)
        return True

    def help_exit(self):
        print("Exit the interpreter.")
        print("You can also use the Ctrl-D shortcut.")
    do_EOF = do_exit
    help_EOF = help_exit


def main():
    cmd_in = InteractiveCmd()

    point = TCP4ClientEndpoint(reactor, "localhost", 5678)
    d = connectProtocol(point, CallcenterQueueClient())
    d.addCallback(cmd_in.gotProtocol)

    reactor.callInThread(cmd_in.cmdloop)

    reactor.run()


if __name__ == "__main__":
    main()
