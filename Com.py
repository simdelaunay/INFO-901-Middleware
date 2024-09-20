import random
from time import sleep
from typing import Callable, List

from Mailbox import Mailbox

from pyeventbus3.pyeventbus3 import PyBus, subscribe, Mode

from Message import *


class Com:
    """
    Classe de communication entre les processus
    """
    def __init__(self, nbProcess):
        self.nbProcess = nbProcess
        self.myId = None
        self.listInitId = []

        self.aliveProcesses = []
        self.maybeAliveProcesses = []
        self.beatCheck = None

        PyBus.Instance().register(self, self)
        sleep(1)

        self.mailbox = Mailbox()
        self.clock = 0

        self.nbSync = 0
        self.isSyncing = False

        self.tokenState = TokenState.Null
        self.currentTokenId = None

        self.isBlocked = False
        self.awaitingFrom = []
        self.recvObj = None

        self.alive = True
        if self.getMyId() == self.nbProcess - 1:
            self.currentTokenId = random.randint(0, 10000 * (self.nbProcess - 1))
            self.sendToken()
        self.startHeartbeat()


    def getNbProcess(self) -> int:
        """
        Retourne le nombre de processus
        :return: int
        """
        return self.nbProcess

    def getMyId(self) -> int:
        """
        Retourne l'ID du processus
        :return: int
        """
        if self.myId is None:
            self.initMyId()
        return self.myId

    def initMyId(self):
        """
        Initialise l'ID du processus
        """
        randomNb = random.randint(0, 10000 * (self.nbProcess - 1))
        print("Mon id aléatoire est:", randomNb)
        self.sendMessage(InitIdMessage(randomNb))
        sleep(2)
        if len(set(self.listInitId)) != self.nbProcess:
            print("Conflit, nouvel essai en cours")
            self.listInitId = []
            return self.initMyId()
        self.listInitId.sort()
        self.myId = self.listInitId.index(randomNb)
        print("Mon id est :", self.myId, "et ma liste est :", self.listInitId, "et mon aléatoire est :", randomNb)

    @subscribe(threadMode=Mode.PARALLEL, onEvent=InitIdMessage)
    def onReceiveInitIdMessage(self, message: InitIdMessage):
        """
        Réception d'un message d'initialisation d'ID
        :param message: InitIdMessage
        """
        print("Message d'initialisation d'ID reçu avec un nombre aléatoire égal à", message.getObject())
        self.listInitId.append(message.getObject())

    def sendMessage(self, message: Message):
        """
        Envoie un message
        :param message: Message
        """
        if not message.is_system:
            self.incClock()
            message.horloge = self.clock
        print(message)
        PyBus.Instance().post(message)

    def sendTo(self, obj: any, com_to: int):
        """
        Envoie un message à un processus
        :param obj: any
        :param com_to: int
        """
        self.sendMessage(MessageTo(obj, self.getMyId(), com_to))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=MessageTo)
    def onReceive(self, message: MessageTo):
        """
        Réception d'un message
        :param message: MessageTo
        """
        if message.to_id != self.getMyId() or type(message) in [MessageToSync, Token, AcknowledgementMessage]:
            return
        if not message.is_system:
            self.clock = max(self.clock, message.horloge) + 1
        print("Message reçu de", message.from_id, ":", message.getObject())
        self.mailbox.addMessage(message)

    def sendToSync(self, obj: any, com_to: int):
        """
        Envoie un message de manière synchrone
        :param obj: any
        :param com_to: int
        """
        self.awaitingFrom = com_to
        self.sendMessage(MessageToSync(obj, self.getMyId(), com_to))
        while com_to == self.awaitingFrom:
            if not self.alive:
                return

    def recevFromSync(self, com_from: int) -> any:
        """
        Réception d'un message de manière synchrone
        :param com_from: int
        :return: any
        """
        self.awaitingFrom = com_from
        while com_from == self.awaitingFrom:
            if not self.alive:
                return
        ret = self.recvObj
        self.recvObj = None
        return ret

    @subscribe(threadMode=Mode.PARALLEL, onEvent=MessageToSync)
    def onReceiveSync(self, message: MessageToSync):
        """
        Réception d'un message de manière synchrone
        :param message: MessageToSync
        """
        if message.to_id != self.getMyId():
            return
        if not message.is_system:
            self.clock = max(self.clock, message.horloge) + 1
        while message.from_id != self.awaitingFrom:
            if not self.alive:
                return
        self.awaitingFrom = -1
        self.recvObj = message.getObject()
        self.sendMessage(AcknowledgementMessage(self.getMyId(), message.from_id))

    def broadcastSync(self, com_from: int, obj: any = None) -> any:
        """
        Broadcast de manière synchrone
        :param com_from: int
        :param obj: any
        :return: any
        """
        if self.getMyId() == com_from:
            print("Broadcast synchronisé", obj)
            for i in range(self.nbProcess):
                if i != self.getMyId():
                    self.sendToSync(obj, i, 99)
        else:
            return self.recevFromSync(com_from)

    @subscribe(threadMode=Mode.PARALLEL, onEvent=AcknowledgementMessage)
    def onAckSync(self, event: AcknowledgementMessage):
        """
        Réception d'un accusé de réception
        :param event: AcknowledgementMessage
        """
        if self.getMyId() == event.to_id:
            print("Accusé de Réception reçu de", event.from_id)
            self.awaitingFrom = -1

    def synchronize(self):
        """
        Synchronisation
        """
        self.isSyncing = True
        print("Synchronisation")
        while self.isSyncing:
            sleep(0.1)
            print("Synchronisation en attente (IN)")
            if not self.alive:
                return
        while self.nbSync != 0:
            sleep(0.1)
            print("Synchronisation en attente (OUT)")
            if not self.alive:
                return
        print("Synchronisé")

    def requestSC(self):
        """
        Demande de la Section critique
        """
        print("Demande de la Section critique")
        self.tokenState = TokenState.Requested
        while self.tokenState == TokenState.Requested:
            if not self.alive:
                return
        print("La Section critique est prise")

    def broadcast(self, obj: any):
        """
        param obj: any
        """
        self.sendMessage(BroadcastMessage(obj, self.getMyId()))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastMessage)
    def onBroadcast(self, message: BroadcastMessage):
        """
        Réception d'un message broadcasté
        :param message: BroadcastMessage
        """
        if message.from_id == self.getMyId() or type(message) in [HeartbeatMessage]:
            return
        print("Message broadcasté reçu de", message.from_id, ":", message.getObject())
        if not message.is_system:
            self.clock = max(self.clock, message.horloge) + 1
        self.mailbox.addMessage(message)

    def sendToken(self):
        """
        Envoie du token
        """
        if self.currentTokenId is None:
            return
        sleep(0.1)
        self.sendMessage(Token(self.getMyId(), ((self.getMyId() + 1) % self.nbProcess + self.nbProcess) % self.nbProcess, self.nbSync, self.currentTokenId))
        self.currentTokenId = None

    def releaseSC(self):
        """
        Relachement de la Section critique
        """
        print("La Section critique est en train d'être relachée")
        if self.tokenState == TokenState.SC:
            self.tokenState = TokenState.Release
        self.sendToken()
        self.tokenState = TokenState.Null
        print("La Section critique a été relachée")

    def incClock(self):
        """
        Incrémentation de l'horloge
        """
        self.clock += 1

    def getClock(self) -> int:
        """
        Retourne l'horloge
        :return: int
        """
        return self.clock

    def stop(self):
        """
        Arrêt du processus
        """
        self.alive = False

    @subscribe(threadMode=Mode.PARALLEL, onEvent=Token)
    def onToken(self, event: Token):
        """
        Réception du token
        :param event: Token
        """
        if event.to_id != self.getMyId() or not self.alive:
            return
        print("Token reçu de", event.from_id)
        self.currentTokenId = event.currentTokenId
        self.nbSync = ((event.nbSync + int(self.isSyncing)) % self.nbProcess + self.nbProcess) % self.nbProcess
        self.isSyncing = False
        if self.tokenState == TokenState.Requested:
            self.tokenState = TokenState.SC
        else:
            self.sendToken()

    def doCriticalAction(self, funcToCall: Callable, *args: List[any]) -> any:
        """
        Action critique
        :param funcToCall: Callable
        :param args: List[any]
        :return: any
        """
        self.requestSC()
        ret = None
        if self.alive:
            if args is None:
                ret = funcToCall()
            else:
                ret = funcToCall(*args)
            self.releaseSC()
        return ret

    def startHeartbeat(self):
        """
        Lancement du heartbeat
        """
        self.sendMessage(StartHeartbeatMessage(self.getMyId()))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=StartHeartbeatMessage)
    def onStartHeartbeat(self, event: StartHeartbeatMessage):
        """
        Réception du message de lancement du heartbeat
        :param event: StartHeartbeatMessage
        """
        if event.from_id != self.getMyId():
            return
        self.heartbeat()

    def heartbeat(self):
        """
        Heartbeat
        """
        print("Lancement heartbeat")
        while self.alive:
            self.sendMessage(HeartbeatMessage(self.getMyId()))
            sleep(0.1)

            self.beatCheck = True
            print("Verification heartbeat")
            print("Processus en vie", self.aliveProcesses)
            print("Processus mort", self.maybeAliveProcesses)
            tmpMaybeAliveProcesses = [idMaybeDead for idMaybeDead in range(self.nbProcess) if idMaybeDead != self.getMyId() and idMaybeDead not in self.aliveProcesses]
            print("Processus peut être en vie", tmpMaybeAliveProcesses)
            self.aliveProcesses = []
            for idDeadProcess in self.maybeAliveProcesses:
                if idDeadProcess < self.getMyId():
                    self.myId -= 1
                    print("Mon id à changé de  ", self.getMyId()+1, "à", self.getMyId())
                tmpMaybeAliveProcesses = [(idMaybeDead - 1 if idMaybeDead > idDeadProcess else idMaybeDead) for idMaybeDead in tmpMaybeAliveProcesses]
                self.nbProcess -= 1
            self.maybeAliveProcesses = tmpMaybeAliveProcesses
            print("Heartbeat Vérifié")
            self.beatCheck = False

    @subscribe(threadMode=Mode.PARALLEL, onEvent=HeartbeatMessage)
    def onHeartbeat(self, event: HeartbeatMessage):
        """
        Réception d'un heartbeat
        :param event: HeartbeatMessage
        """
        while self.beatCheck:
            pass
        if event.from_id == self.getMyId():
            return
        print("Heartbeat reçu de", event.from_id)
        if event.from_id in self.maybeAliveProcesses:
            self.maybeAliveProcesses.remove(event.from_id)
        if event.from_id not in self.aliveProcesses:
            self.aliveProcesses.append(event.from_id)
