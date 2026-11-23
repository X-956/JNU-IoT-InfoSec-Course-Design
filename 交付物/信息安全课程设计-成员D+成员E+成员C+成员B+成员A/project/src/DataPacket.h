#ifndef DATAPACKET_H
#define DATAPACKET_H

#include <omnetpp.h>

using namespace omnetpp;

/**
 * 星间网络业务包：携带源、目的、序号、跳数和生成时间。
 * 用 cPacket 是为了让 Qtenv/统计能感知包长。
 */
class DataPacket : public cPacket
{
  private:
    int src = 0;
    int dst = 0;
    int seq = 0;
    int hops = 0;
    simtime_t createdAt;
    std::string path;

  public:
    DataPacket(const char *name = nullptr) : cPacket(name) {}
    virtual ~DataPacket() {}

    int getSrc() const { return src; }
    int getDst() const { return dst; }
    int getSeq() const { return seq; }
    int getHops() const { return hops; }
    simtime_t getCreatedAt() const { return createdAt; }
    const std::string& getPath() const { return path; }
    void visit(int id) { if (!path.empty()) path += "-"; path += std::to_string(id); }

    void setSrc(int v) { src = v; }
    void setDst(int v) { dst = v; }
    void setSeq(int v) { seq = v; }
    void setHops(int v) { hops = v; }
    void setCreatedAt(simtime_t v) { createdAt = v; }

    virtual DataPacket *dup() const override { return new DataPacket(*this); }
};

#endif
