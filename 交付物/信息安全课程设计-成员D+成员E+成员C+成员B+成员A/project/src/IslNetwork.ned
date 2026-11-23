// 由 scripts/generate_topology.py 自动生成；不要手工改连接。
network IslNetwork
{
    submodules:
        sat[24]: Satellite;
        controller: NetworkController { numSats = 24; }
    connections:
        sat[0].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[1].isl++;
        sat[0].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[7].isl++;
        sat[0].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[8].isl++;
        sat[1].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[2].isl++;
        sat[1].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[9].isl++;
        sat[2].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[3].isl++;
        sat[2].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[10].isl++;
        sat[3].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[4].isl++;
        sat[3].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[11].isl++;
        sat[4].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[5].isl++;
        sat[4].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[12].isl++;
        sat[5].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[6].isl++;
        sat[5].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[13].isl++;
        sat[6].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[7].isl++;
        sat[6].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[14].isl++;
        sat[7].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[15].isl++;
        sat[8].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[9].isl++;
        sat[8].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[15].isl++;
        sat[8].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[16].isl++;
        sat[9].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[10].isl++;
        sat[9].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[17].isl++;
        sat[10].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[11].isl++;
        sat[10].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[18].isl++;
        sat[11].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[12].isl++;
        sat[11].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[19].isl++;
        sat[12].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[13].isl++;
        sat[12].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[20].isl++;
        sat[13].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[14].isl++;
        sat[13].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[21].isl++;
        sat[14].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[15].isl++;
        sat[14].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[22].isl++;
        sat[15].isl++ <--> ned.DelayChannel { delay = 120ms; } <--> sat[23].isl++;
        sat[16].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[17].isl++;
        sat[16].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[23].isl++;
        sat[17].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[18].isl++;
        sat[18].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[19].isl++;
        sat[19].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[20].isl++;
        sat[20].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[21].isl++;
        sat[21].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[22].isl++;
        sat[22].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[23].isl++;
}
