#include "Satellite.h"
#include "DataPacket.h"
#include "NetworkController.h"

#include <cmath>

Define_Module(Satellite);

Satellite::~Satellite()
{
    if (sendTimer != nullptr)
        cancelAndDelete(sendTimer);
}

void Satellite::initialize()
{
    nodeId = getIndex();

    int n = getParentModule()->getSubmoduleVectorSize("sat");
    destId = par("destId").intValue();
    if (destId < 0)
        destId = (nodeId + n / 2) % n;

    sendInterval = par("sendInterval").doubleValueInUnit("s");
    startTime = par("startTime").doubleValueInUnit("s");
    stopTime = par("stopTime").doubleValueInUnit("s");
    if (sendInterval <= 0 || stopTime < startTime || startTime < 0)
        throw cRuntimeError("Invalid traffic time parameters");
    failed = par("failed").boolValue();

    for (int g = 0; g < gateSize("isl"); ++g) {
        cGate *out = gate("isl$o", g);
        cModule *neighbor = out->getNextGate()->getOwnerModule();
        int id = neighbor->getIndex();
        neighborByGate[g] = id;
        gateByNeighbor[id] = g;
    }

    getDisplayString().setTagArg("i", 1, failed ? "red" : "green");
    getDisplayString().setTagArg("t", 0, ("S" + std::to_string(nodeId)).c_str());

    // 24 节点按 3 轨道面 x 8 时隙排成网格；4 节点排成环形，便于 Qtenv 观察。
    if (n == 24) {
        int plane = nodeId / 8;
        int slot = nodeId % 8;
        getDisplayString().setTagArg("p", 0, 80 + plane * 160);
        getDisplayString().setTagArg("p", 1, 40 + slot * 55);
    }
    else {
        const double pi = 3.14159265358979323846;
        double angle = 2.0 * pi * nodeId / n;
        getDisplayString().setTagArg("p", 0, (int)(300 + 150 * std::cos(angle)));
        getDisplayString().setTagArg("p", 1, (int)(300 + 150 * std::sin(angle)));
    }

    sendTimer = new cMessage("sendTimer");
    if (!failed)
        scheduleAt(SimTime(startTime), sendTimer);
}

int Satellite::getNeighborId(int gateIndex) const
{
    auto it = neighborByGate.find(gateIndex);
    return it == neighborByGate.end() ? -1 : it->second;
}

double Satellite::getLinkDelay(int gateIndex)
{
    cGate *g = gate("isl$o", gateIndex);
    cChannel *ch = g == nullptr ? nullptr : g->getChannel();
    if (ch != nullptr && ch->hasPar("delay"))
        return ch->par("delay").doubleValueInUnit("s");
    return 0.001;
}

void Satellite::setFailed(bool value)
{
    failed = value;
    getDisplayString().setTagArg("i", 1, failed ? "red" : "green");
}

void Satellite::setNextHop(int dst, int gateIndex)
{
    nextHop[dst] = gateIndex;
}

void Satellite::clearRoutes()
{
    nextHop.clear();
}

void Satellite::sendData()
{
    DataPacket *pkt = new DataPacket("data");
    pkt->setSrc(nodeId);
    pkt->setDst(destId);
    pkt->setSeq(sent);
    pkt->setHops(0);
    pkt->setCreatedAt(simTime());
    pkt->setByteLength(1024);
    sent++;
    pkt->visit(nodeId);
    check_and_cast<NetworkController *>(getParentModule()->getSubmodule("controller"))->packetSent(pkt);
    forwardPacket(pkt);
}

void Satellite::forwardPacket(DataPacket *pkt)
{
    auto it = nextHop.find(pkt->getDst());
    if (it == nextHop.end()) {
        dropped++;
        check_and_cast<NetworkController *>(getParentModule()->getSubmodule("controller"))->packetEnded(pkt, "no_route");
        delete pkt;
        return;
    }

    pkt->setHops(pkt->getHops() + 1);
    send(pkt, "isl$o", it->second);
}

void Satellite::handleMessage(cMessage *msg)
{
    if (msg == sendTimer) {
        if (!failed && simTime().dbl() <= stopTime)
            sendData();

        if (simTime().dbl() + sendInterval <= stopTime)
            scheduleAt(simTime() + SimTime(sendInterval), sendTimer);
        return;
    }

    DataPacket *pkt = dynamic_cast<DataPacket *>(msg);
    if (pkt == nullptr) {
        delete msg;
        return;
    }

    if (failed) {
        dropped++;
        pkt->visit(nodeId);
        check_and_cast<NetworkController *>(getParentModule()->getSubmodule("controller"))->packetEnded(pkt, "failed_node");
        delete pkt;
        return;
    }

    pkt->visit(nodeId);
    if (pkt->getDst() == nodeId) {
        received++;
        delaySum += simTime() - pkt->getCreatedAt();
        hopSum += pkt->getHops();
        check_and_cast<NetworkController *>(getParentModule()->getSubmodule("controller"))->packetEnded(pkt, "received");
        delete pkt;
        return;
    }

    forwardPacket(pkt);
}

void Satellite::finish()
{
    recordScalar("sent", sent);
    recordScalar("received", received);
    recordScalar("dropped", dropped);
    recordScalar("delaySum", delaySum.dbl());
    recordScalar("hopSum", hopSum);
    recordScalar("failed", failed ? 1 : 0);
    recordScalar("meanDelay", received > 0 ? delaySum.dbl() / received : 0.0);
    recordScalar("meanHops", received > 0 ? (double)hopSum / received : 0.0);
}
