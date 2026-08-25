from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'slam'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.lua')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_link='user@todo.todo',
    description='SLAM and sensor bridging launch package',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'drone_teleop = slam.drone_teleop:main',
            'odom_to_tf_relay = slam.odom_to_tf:main',
        ],
    },
)