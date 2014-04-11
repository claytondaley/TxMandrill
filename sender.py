from StringIO import StringIO
from OpenSSL.SSL import SSLv3_METHOD

from twisted.mail.smtp import ESMTPSenderFactory
from twisted.internet.ssl import ClientContextFactory
from twisted.internet.defer import Deferred
from twisted.internet import reactor

class MandrillSender():

    def __init__(self, username, secret, smtpHost='smtp.mandrillapp.com', smtpPort=587):
        self.username = username
        self.secret = secret
        self.smtpHost = smtpHost
        self.smtpPort = smtpPort

    def sendmail(self, fromAddress, toAddress, message):
        """
        @param fromAddress: The SMTP reverse path (ie, MAIL FROM)
        @param toAddress: The SMTP forward path (ie, RCPT TO)
        @param message: A file-like object containing the headers and body of
        the message to send.

        @return: A Deferred which will be called back when the message has been
        sent or which will errback if it cannot be sent.
        """

        if not hasattr(message, 'read'):
            # It's not a file
            message = StringIO(str(message))

        def cancel(d):
            """
            Cancel the L{mandrill.sendmail} call, tell the factory not to
            retry and disconnect the connection.

            @param d: The L{defer.Deferred} to be cancelled.
            """
            senderFactory.sendFinished = True
            if senderFactory.currentProtocol:
                senderFactory.currentProtocol.transport.abortConnection()
            else:
                # Connection hasn't been made yet
                connector.disconnect()

        # Create a context factory which only allows SSLv3 and does not verify
        # the peer's certificate.
        contextFactory = ClientContextFactory()
        contextFactory.method = SSLv3_METHOD

        resultDeferred = Deferred()

        senderFactory = ESMTPSenderFactory(
            self.username,
            self.secret,
            fromAddress,
            toAddress,
            message,
            resultDeferred,
            contextFactory=contextFactory)

        connector = reactor.connectTCP(self.smtpHost, self.smtpPort, senderFactory)

        return resultDeferred