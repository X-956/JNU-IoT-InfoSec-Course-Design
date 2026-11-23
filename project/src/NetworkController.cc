#include "NetworkController.h"
#include "DataPacket.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <queue>
#include <sstream>
#include <iomanip>

Define_Module(NetworkController);

NetworkController::~NetworkController()
{
    if (failureMsg != nullptr)
        cancelAndDelete(failureMsg);
    if (recoverMsg != nullptr)
        cancelAndDelete(recoverMsg);
}

void NetworkController::initialize()
{
    numSats = par("numSats").intValue();
    for (int i = 0; i < numSats; ++i)
        sats.push_back(check_and_cast<Satellite *>(getParentModule()->getSubmodule("sat", i)));

    buildGraph();
    computeRoutes();

    failureEnabled = par("failureEnabled").boolValue();
    recoveryEnabled = par("recoveryEnabled").boolValue();
    failureTime = SimTime(par("failureTime").doubleValueInUnit("s"));
    detectionDelay = SimTime(par("detectionDelay").doubleValueInUnit("s"));
    failureNodes = par("failureNodes").stdstringValue();
    failureMode = par("failureMode").stdstringValue();
    failureK = par("failureK").intValue();
    std::string traceName = par("traceFile").stdstringValue();
    if (!traceName.empty()) {
        trace.open(traceName);
        if (!trace) throw cRuntimeError("Cannot open packet trace: %s", traceName.c_str());
        trace << "time,created,src,dst,seq,status,path,delay,hops\n";
        trace << std::setprecision(12);
    }

    EV_INFO << "controller params: failureEnabled=" << failureEnabled
            << " failureTime=" << failureTime
            << " detectionDelay=" << detectionDelay
            << " failureNodes=[" << failureNodes << "]\n";

    recoverMsg = new cMessage("recover");
    recoverMsg->setSchedulingPriority(-10);
    if (failureEnabled) {
        failureMsg = new cMessage("failure");
        failureMsg->setSchedulingPriority(-10);
        scheduleAt(failureTime, failureMsg);
        EV_INFO << "Failure scheduled at " << failureTime
                << " for nodes [" << failureNodes << "]\n";
    }
}

void NetworkController::buildGraph()
{
    adj.assign(numSats, {});
    gateByNeighbor.clear();

    for (int i = 0; i < numSats; ++i) {
        int degree = sats[i]->gateSize("isl");
        for (int g = 0; g < degree; ++g) {
            int nb = sats[i]->getNeighborId(g);
            if (nb < 0)
                continue;
            // 链路代价 = 传播时延；路径选择因此是“最短时延”。
            double w = sats[i]->getLinkDelay(g);
            adj[i][nb] = w;
            gateByNeighbor[{i, nb}] = g;
        }
    }
    EV_INFO << "graph built: " << numSats << " nodes, sample link delay="
            << (adj[0].empty() ? -1.0 : adj[0].begin()->second) << " s\n";
}

void NetworkController::computeRoutes()
{
    const double INF = std::numeric_limits<double>::infinity();

    for (int i = 0; i < numSats; ++i)
        sats[i]->clearRoutes();

    for (int src = 0; src < numSats; ++src) {
        if (sats[src]->isFailed())
            continue;

        std::vector<double> dist(numSats, INF);
        std::vector<int> prev(numSats, -1);
        std::vector<bool> done(numSats, false);
        dist[src] = 0.0;

        for (int iter = 0; iter < numSats; ++iter) {
            int u = -1;
            double best = INF;
            for (int i = 0; i < numSats; ++i) {
                if (!done[i] && dist[i] < best) {
                    best = dist[i];
                    u = i;
                }
            }
            if (u < 0)
                break;
            done[u] = true;

            for (const auto &edge : adj[u]) {
                int v = edge.first;
                double w = edge.second;
                if (sats[v]->isFailed())
                    continue;
                if (dist[u] + w < dist[v]) {
                    dist[v] = dist[u] + w;
                    prev[v] = u;
                }
            }
        }

        for (int dst = 0; dst < numSats; ++dst) {
            if (dst == src || sats[dst]->isFailed() || !std::isfinite(dist[dst]))
                continue;

            int cur = dst;
            while (prev[cur] != -1 && prev[cur] != src)
                cur = prev[cur];

            if (prev[cur] == src) {
                auto it = gateByNeighbor.find({src, cur});
                if (it != gateByNeighbor.end())
                    sats[src]->setNextHop(dst, it->second);
            }
        }
    }
}

void NetworkController::applyFailure()
{
    failedCount = 0;

    if (failureMode == "random") {
        std::vector<int> candidates;
        for (int i = 0; i < numSats; ++i)
            if (!sats[i]->isFailed())
                candidates.push_back(i);

        int toRemove = std::min(failureK, (int)candidates.size());
        for (int n = 0; n < toRemove; ++n) {
            int idx = intrand(candidates.size());
            int id = candidates[idx];
            candidates.erase(candidates.begin() + idx);
            sats[id]->setFailed(true);
            failedCount++;
        }
    }
    else {
        std::stringstream ss(failureNodes);
        std::string token;
        while (std::getline(ss, token, ',')) {
            if (token.empty())
                continue;
            int id = std::stoi(token);
            if (id >= 0 && id < numSats && !sats[id]->isFailed()) {
                sats[id]->setFailed(true);
                failedCount++;
            }
        }
    }

    recordConnectivity();

    sentAtFailure = 0;
    receivedAtFailure = 0;
    for (int i = 0; i < numSats; ++i) {
        sentAtFailure += sats[i]->getSent();
        receivedAtFailure += sats[i]->getReceived();
    }

    EV_INFO << "Applied failure to " << failedCount << " nodes; LCC="
            << lccAfterFailure << ", components=" << componentsAfterFailure << "\n";
}

void NetworkController::recordConnectivity()
{
    std::vector<bool> visited(numSats, false);
    int best = 0;
    int components = 0;

    for (int start = 0; start < numSats; ++start) {
        if (sats[start]->isFailed() || visited[start])
            continue;

        components++;
        int count = 0;
        std::queue<int> q;
        q.push(start);
        visited[start] = true;
        while (!q.empty()) {
            int u = q.front();
            q.pop();
            count++;
            for (const auto &edge : adj[u]) {
                int v = edge.first;
                if (!sats[v]->isFailed() && !visited[v]) {
                    visited[v] = true;
                    q.push(v);
                }
            }
        }
        best = std::max(best, count);
    }

    lccAfterFailure = best;
    componentsAfterFailure = components;
}

void NetworkController::handleMessage(cMessage *msg)
{
    if (msg == failureMsg) {
        applyFailure();
        if (recoveryEnabled)
            scheduleAt(simTime() + detectionDelay, recoverMsg);
        return;
    }

    if (msg == recoverMsg) {
        routeUpdateDelay = simTime() - failureTime;
        computeRoutes();
        EV_INFO << "Routes recomputed at " << simTime()
                << " (routeUpdateDelay=" << routeUpdateDelay << ")\n";
        return;
    }

    delete msg;
}

void NetworkController::finish()
{
    if (trace.is_open()) trace.close();
    long planned = 0;
    for (auto *sat : sats) {
        double start = sat->par("startTime").doubleValueInUnit("s");
        double stop = sat->par("stopTime").doubleValueInUnit("s");
        double interval = sat->par("sendInterval").doubleValueInUnit("s");
        planned += stop >= start ? (long)std::floor((stop-start)/interval + 1e-9) + 1 : 0;
    }
    recordScalar("plannedPackets", planned);
    recordScalar("observationDuration", simTime().dbl());
    recordScalar("numSats", numSats);
    recordScalar("failedCount", failedCount);
    if (lccAfterFailure >= 0) {
        recordScalar("lccAfterFailure", lccAfterFailure);
        recordScalar("componentsAfterFailure", componentsAfterFailure);

        long sentFinal = 0;
        long receivedFinal = 0;
        for (int i = 0; i < numSats; ++i) {
            sentFinal += sats[i]->getSent();
            receivedFinal += sats[i]->getReceived();
        }
        long sentAfter = sentFinal - sentAtFailure;
        long receivedAfter = receivedFinal - receivedAtFailure;
        recordScalar("sentBeforeFailure", sentAtFailure);
        recordScalar("receivedBeforeFailure", receivedAtFailure);
        recordScalar("sentAfterFailure", sentAfter);
        recordScalar("receivedAfterFailureLegacy", receivedAfter);
        recordScalar("sentAfterFailureCohort", cohortSent);
        recordScalar("receivedAfterFailureCohort", cohortReceived);
        recordScalar("pdrAfterFailure",
                     cohortSent > 0 ? 100.0 * cohortReceived / cohortSent : 0.0);
        if (routeUpdateDelay >= 0)
            recordScalar("routeUpdateDelay", routeUpdateDelay.dbl());
    }
}

void NetworkController::packetSent(DataPacket *pkt)
{
    if (failureEnabled && pkt->getCreatedAt() >= failureTime) cohortSent++;
}

void NetworkController::packetEnded(DataPacket *pkt, const char *status)
{
    if (failureEnabled && pkt->getCreatedAt() >= failureTime && std::string(status)=="received")
        cohortReceived++;
    if (trace.is_open())
        trace << simTime().dbl() << ',' << pkt->getCreatedAt().dbl() << ','
              << pkt->getSrc() << ',' << pkt->getDst() << ',' << pkt->getSeq() << ','
              << status << ',' << pkt->getPath() << ','
              << (simTime()-pkt->getCreatedAt()).dbl() << ',' << pkt->getHops() << '\n';
}
