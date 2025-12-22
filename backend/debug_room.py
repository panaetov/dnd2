import asyncio
import logging
import ssl

from slixmpp import ClientXMPP

logger = logging.getLogger(__name__)


class EchoBot(ClientXMPP):

    def __init__(self, jid, password, room, nick):
        ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick

        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)

        self.register_plugin("xep_0045")

        # If you wanted more functionality, here's how to register plugins:
        # self.register_plugin('xep_0030') # Service Discovery
        # self.register_plugin('xep_0199') # XMPP Ping

        # Here's how to access plugins once you've registered them:
        # self['xep_0030'].add_feature('echo_demo')

        # If you are working with an OpenFire server, you will
        # need to use a different SSL version:
        # import ssl
        # self.ssl_version = ssl.PROTOCOL_SSLv3

    async def session_start(self, event):
        await self.get_roster()
        self.send_presence()
        self.plugin["xep_0045"].join_muc(self.room, self.nick)

        import pdb

        pdb.set_trace()
        ...
        # Most get_*/set_* methods from plugins use Iq stanzas, which
        # can generate IqError and IqTimeout exceptions
        #
        # try:
        #     self.get_roster()
        # except IqError as err:
        #     logging.error('There was an error getting the roster')
        #     logging.error(err.iq['error']['condition'])
        #     self.disconnect()
        # except IqTimeout:
        #     logging.error('Server is taking too long to respond')
        #     self.disconnect()

    def message(self, msg):
        logger.info(f"New message: {msg}, {type(msg)}")
        msg.reply(f"Thanks {msg['from']} for sending message:\n{msg['body']}").send()


if __name__ == "__main__":
    # Ideally use optparse or argparse to get JID,
    # password, and log level.

    logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s %(message)s")

    xmpp = EchoBot("panaetov@meet.jitsi", "", "123@muc.meet.jitsi", "bot")

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    xmpp.connect("51.250.102.96", 5222)
    asyncio.get_event_loop().run_forever()
