simple Satellite
{
    parameters:
        int destId = default(-1);
        volatile double sendInterval @unit(s) = default(1s);
        volatile double startTime @unit(s) = default(1s);
        volatile double stopTime @unit(s) = default(20s);
        bool failed = default(false);
        @display("i=block/routing");
    gates:
        inout isl[];
}
