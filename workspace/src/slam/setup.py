from setuptools import setup
import os
from glob import glob

package_name = 'slam'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='ph1251320@physics.iitd.ac.in',
    description='SLAM package with 2D LiDAR visualization',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
    'console_scripts': [
        'drone_teleop = slam.drone_teleop:main',
        'odom_to_tf_relay = slam.odom_to_tf:main',
        'safety_filter = slam.safety_filter:main',
        'gz_direct_bridge = slam.gz_direct_bridge:main',
    ],
},
)
