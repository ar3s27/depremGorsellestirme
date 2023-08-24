from yowsup.layers.auth import YowAuthenticationProtocolLayer
from yowsup.layers import YowLayerEvent
from yowsup.layers import YowParallelLayer
from yowsup.layers import YowLayer
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
from yowsup.layers.protocol_presence.protocolentities import PresenceProtocolEntity
from yowsup.layers.protocol_chatstate import OutgoingChatstateProtocolEntity
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers.network import YowTransportLayer
from yowsup.stacks import YowStack, YowStackBuilder
from yowsup import env

class EchoLayer(YowParallelLayer):

    def __init__(self):
        super(EchoLayer, self).__init__()
        self.ackQueue = []

    def receive(self, event):
        if event.getName() == YowNetworkLayer.EVENT_STATE_CONNECT:
            self.ackQueue = []

        if event.getName() == YowLayer.EVENT_RECEIVE:
            self.onReceiveMessage(event)

        self.broadcast(event)

    def onReceiveMessage(self, event):
        if event.getName() == "message":
            message = TextMessageProtocolEntity(
                event.getArg("message").getBody(),
                to=event.getArg("from"),
                _from=event.getArg("to")
            )
            self.ackQueue.append(message.ack())
            self.broadcast(message)
            self.ackQueue.append(message.ack())
            outgoingChatstate = OutgoingChatstateProtocolEntity(
                OutgoingChatstateProtocolEntity.STATE_TYPING,
                to=event.getArg("from")
            )
            self.broadcast(outgoingChatstate)

# Your WhatsApp number and password
credentials = ("your_phone_number", "your_password")

stackBuilder = YowStackBuilder()

stack = stackBuilder\
    .pushDefaultLayers(True)\
    .push(EchoLayer)\
    .build()

stack.setCredentials(credentials)
stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))

try:
    stack.loop()
except KeyboardInterrupt:
    stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_DISCONNECT))
