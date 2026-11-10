# Flight controller setup to accept visual odometry in GPS denied environment for localization

The process is essentially 3 steps
1. Give an initial GPS origin to the flight controller so that it has a reference
2. Make sure the given parameters are correctly set so that Ardupilot expects visual odometry
3. Provide the visual odometry on the `/mavros/odometry/out` topic. See `cartographer_odom_bridge.py` for the details but the implementation expects the TF2 frames `odom <-> base_link` to work (is provided by cartographer slam in this case).


## 1. Initial pose

There are two ways to do it (must be done on every boot of the ardupilot firmware)
- Manually using the MAVLINK console
```bash
module load message
message SET_GPS_GLOBAL_ORIGIN 0 -353621474 1491651746 600000 0
```

- Publishing to the ros topic `/mavros/global_position/set_gp_origin` (Put in the launch file with a 10 second timer so it only publishes after mavros is completely up and running)
```py3
set_ekf_origin = TimerAction(
    period=10.0,
    actions=[
        ExecuteProcess(
            cmd=[
                'ros2', 'topic', 'pub', '--once',
                '/mavros/global_position/set_gp_origin',
                'geographic_msgs/msg/GeoPointStamped',
                r'{position: {latitude: -35.3621474, longitude: 149.1651746, altitude: 600.0}}'
            ],
            output='screen'
        )
    ]
)
```


## 2. Ardupilot parameters

```bash
param set AHRS_EKF_TYPE 3
param set EK2_ENABLE 0
param set EK3_ENABLE 1

param set VISO_TYPE 1

param set EK3_SRC1_POSXY 6
param set EK3_SRC1_VELXY 0
param set EK3_SRC1_POSZ 1
param set EK3_SRC1_VELZ 0
param set EK3_SRC1_YAW 6

param set GPS1_TYPE 0

param set VISO_POS_X 0
param set VISO_POS_Y 0
param set VISO_POS_Z 0
```

- First three enable the EKF3 mode instead of EKF2.
- VISO_TYPE=1 indicates that we want to accept visual odometry via MAVLINK
- SRC1 indicates primary sensor; 0 - None; 1 - Barometer; 2 - Rangefinder; 3 - GPS; 6 - External.
- GPS1_TYPE=0 disables the GPS driver.
- Providing velocity externally caused to drift and crash the drone in simulation hence it seems it is better to let the flight controller calculate it by itself.
- VISO_POS_X,Y,Z are the offsets of the local body positions from the specified GPS origin.
- All of these are permanent between reboots of the firmware.


## 3. Publishing to /mavros/odometry/out

- This must be obtained from the localization algorithm being used using the onboard sensors
- This pose then must be published at a sufficiently high rate in order for ardupilot to be able to hold its position well. Target atleast 20-30 Hz. Higher speeds require higher publish rate.
