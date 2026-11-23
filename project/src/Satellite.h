#ifndef SATELLITE_H
#define SATELLITE_H

#include <omnetpp.h>
#include <map>
#include <string>

using namespace omnetpp;

class DataPacket;

class Satellite : public cSimpleModule
{
  private:
    int nodeId = -1;
    int destId = -1;
    double sendInterval = 1.0;
    double startTime = 1.0;
    double stopTime = 20.0;
    bool failed = false;

    cMessage *sendTimer = nullptr;
    std::map<int, int> neighborByGate;   // 本地 gate 索引 -> 邻居 nodeId
    std::map<int, int> gateByNeighbor;   // 邻居 nodeId -> 本地 gate 索引
    std::map<int, int> nextHop;          // 目的 nodeId -> 本地 gate 索引

    long sent = 0;
    long received = 0;
    long dropped = 0;
    long hopSum = 0;
    simtime_t delaySum = 0;

  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    virtual void finish() override;
    virtual ~Satellite();

  public:
    int getNodeId() const { return nodeId; }
    bool isFailed() const { return failed; }
    int getNeighborId(int gateIndex) const;
    double getLinkDelay(int gateIndex);
    long getSent() const { return sent; }
    long getReceived() const { return received; }
    void setFailed(bool value);
    void setNextHop(int dst, int gateIndex);
    void clearRoutes();
    void sendData();
    void forwardPacket(DataPacket *pkt);
};

#endif
