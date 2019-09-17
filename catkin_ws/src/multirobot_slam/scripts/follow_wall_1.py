#! /usr/bin/env python

# import ros stuff
import rospy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from tf import transformations
from std_srvs.srv import *

import math

active_ = False
pub_ = None
regions_ = {
        'right': 0,
        'fright': 0,
        'front': 0,
        'fleft': 0,
        'left': 0,
}
state_ = 0
state_dict_ = {
    0: 'find the wall',
    1: 'turn left',
    2: 'follow the wall',
}

def wall_follower_switch(req):
    global active_
    active_ = req.data
    res = SetBoolResponse()
    res.success = True
    return res

def clbk_laser(msg):
    global regions_
    regions_ = {
        'right':  min(min(msg.ranges[0:143]), 10),
        'fright': min(min(msg.ranges[144:287]), 10),
        'front':  min(min(msg.ranges[288:431]), 10),
        'fleft':  min(min(msg.ranges[432:575]), 10),
        'left':   min(min(msg.ranges[576:719]), 10),
    }
    take_action()

def change_state(state):
    global state_, state_dict_
    if state is not state_:
        print 'Wall follower - [%s] - %s' % (state, state_dict_[state])
        state_ = state

def take_action():
    global regions_
    regions = regions_
    msg = Twist()
    linear_x = 0
    angular_z = 0

    state_description = ''

    # desirable distance to the wall
    dist = 1.5

    # 8 possible robot cases depending on the distance from different angles

    if regions['front'] > dist and regions['fleft'] > dist and regions['fright'] > dist:
        state_description = 'find the wall'
        change_state(0)

    elif regions['front'] > dist and regions['fleft'] < dist and regions['fright'] < dist:
        state_description = 'find the wall'
        change_state(0)

    elif regions['front'] > dist and regions['fleft'] < dist and regions['fright'] > dist:
        state_description = 'find the wall'
        change_state(0)

    elif regions['front'] < dist and regions['fleft'] > dist and regions['fright'] > dist:
        state_description = 'turn left'
        change_state(1)

    elif regions['front'] < dist and regions['fleft'] > dist and regions['fright'] < dist:
        state_description = 'turn left'
        change_state(1)

    elif regions['front'] < dist and regions['fleft'] < dist and regions['fright'] > dist:
        state_description = 'turn left'
        change_state(1)

    elif regions['front'] < dist and regions['fleft'] < dist and regions['fright'] < dist:
        state_description = 'turn left'
        change_state(1)

    elif regions['front'] > dist and regions['fleft'] > dist and regions['fright'] < dist:
        state_description = 'follow the wall'
        change_state(2)

    else:
        state_description = 'unknown case'
        rospy.loginfo(regions)


def find_wall():
    msg = Twist()
    # velocities
    msg.linear.x = 0.2
    msg.angular.z = -0.3
    return msg

def turn_left():
    msg = Twist()
    msg.angular.z = 0.3
    return msg

def follow_the_wall():
    global regions_

    msg = Twist()
    msg.linear.x = 0.5
    return msg

def main():
    global pub_, active_

    rospy.init_node('reading_laser')

    pub_ = rospy.Publisher('robot1/cmd_vel', Twist, queue_size=1)

    sub = rospy.Subscriber('robot1/base_scan', LaserScan, clbk_laser)

    srv = rospy.Service('wall_follower_switch', SetBool, wall_follower_switch)

    rate = rospy.Rate(20)
    while not rospy.is_shutdown():
        if not active_:
            rate.sleep()
            continue

        msg = Twist()
        if state_ == 0:
            msg = find_wall()
        elif state_ == 1:
            msg = turn_left()
        elif state_ == 2:
            msg = follow_the_wall()
            pass
        else:
            rospy.logerr('Error - unknown state!')

        pub_.publish(msg)

        rate.sleep()

if __name__ == '__main__':
    main()