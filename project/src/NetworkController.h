#ifndef NETWORKCONTROLLER_H
#define NETWORKCONTROLLER_H

#include <omnetpp.h>
#include <map>
#include <string>
#include <utility>
#include <vector>
#include <fstream>

#include "Satellite.h"

using namespace omnetpp;

/**
 * 简化集中式路由控制器：维护全局拓扑、运行 Dijkstra、下发下一跳；
 * 在 failureTime 标记失效节点，经过 detectionDelay 后重算路由。
 */
class NetworkController : public cSimpleModule
{
  private:
    int numSats = 0;
    std::vector<Satellite *> sats;
    std::vector<std::map<int, double>> adj;
    std::map<std::pair<int, int>, int> gateByNeighbor;

    bool failureEnabled = false;
    bool recoveryEnabled = true;
    simtime_t failureTime = 0;
    simtime_t detectionDelay = 0;
    std::string failureNodes;
    std::string failureMode;
    int failureK = 0;

    cMessage *failureMsg = nullptr;
    cMessage *recoverMsg = nullptr;

    int lccAfterFailure = -1;
    int componentsAfterFailure = -1;
    int failedCount = 0;
    long sentAtFailure = 0;
    long receivedAtFailure = 0;
    simtime_t routeUpdateDelay = -1;
    long cohortSent = 0, cohortReceived = 0;
    std::ofstream trace;

  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    virtual void finish() override;
    virtual ~NetworkController();

  public:
    void packetSent(DataPacket *pkt);
    void packetEnded(DataPacket *pkt, const char *status);
    void buildGraph();
    void computeRoutes();
    void applyFailure();
    void recordConnectivity();
};

#endif
