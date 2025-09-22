#!/usr/bin/env python3

import rospy
import requests  # Import thư viện requests để thực hiện HTTP requests

from std_msgs.msg import String

# def send_get_request(url):
#     response = requests.get(url)
#     return response.text

def send_post_request(url, data):
    headers = {'Content-type': 'application/json'}
    response = requests.post(url, json=data, headers=headers)
    return response.text

def api_request_node():
    rospy.init_node('api_request_node', anonymous=True)
    rate = rospy.Rate(1)  # Tạo một rate 1Hz

    while not rospy.is_shutdown():
        # Gửi HTTP GET request
        # get_url = "https://api.example.com/get_data"
        # get_response = send_get_request(get_url)
        # rospy.loginfo("GET Response: %s", get_response)

        # Gửi HTTP POST request
        post_url = "http://10.14.7.15:1234/api/LogRobot"
        post_data = {
                    "name": "ahihi",
                    "detail": "ahehe",
                    "type": "ahoho",
                    "createdDate": "2023/08/09 15:09:09"
                    }
        post_response = send_post_request(post_url, post_data)
        rospy.loginfo("POST Response: %s", post_response)

        rate.sleep()

if __name__ == '__main__':
    try:
        api_request_node()
    except rospy.ROSInterruptException:
        pass