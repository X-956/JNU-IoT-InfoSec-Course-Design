network FourNodeNetwork
{
    submodules:
        sat[4]: Satellite;
        controller: NetworkController {
            numSats = 4;
        }
    connections:
        sat[0].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[1].isl++;
        sat[1].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[2].isl++;
        sat[2].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[3].isl++;
        sat[3].isl++ <--> ned.DelayChannel { delay = 70ms; } <--> sat[0].isl++;
}
