simple NetworkController
{
    parameters:
        int numSats;
        bool failureEnabled = default(false);
        bool recoveryEnabled = default(true);
        volatile double failureTime @unit(s) = default(40s);
        volatile double detectionDelay @unit(s) = default(2s);
        string failureNodes = default("");
        string failureMode = default("list");
        int failureK = default(0);
        string traceFile = default(""); // optional terminal packet CSV
        @display("i=block/cogwheel");
}
