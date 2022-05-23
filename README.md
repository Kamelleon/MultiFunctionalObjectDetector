# ObjectDetector
Object detector based on YOLOv5 that save pictures locally and gives access to them by flask website.

# App possibilities
- Performing detections from camera frames using G-streamer and RTSP IP link
- Support for h264 and h265 RTSP streams
- Support for multiple stream cameras (defined in "conf.yaml" file)
- Sending messages with images on Telegram
- Informing about current cameras status (online/offline) and detector status (up/down) on Telegram
- Giving access to all performed detections through Flask-based website
- Giving possibility to turn off/turn on detector by using Supla device input (https://www.supla.org/)
- Giving possibility to activate Supla outputs
- Sending information to the database about current detector status (up/down)

# Performance
Program is able to perform detections on 33 RTSP streams in 5 seconds on medium class computer (GTX 750 - 1GB VRAM, Intel Core i5)

# Preview
- Detector

![person_detected](https://github.com/Kamelleon/ObjectDetector/blob/main/preview_screens/detect%20(1).jpg)


- Telegram messages system<br /><br />
![telegram_message](https://github.com/Kamelleon/ObjectDetector/blob/main/preview_screens/detect%20(1).png)


- Website

![main_website](https://github.com/Kamelleon/ObjectDetector/blob/main/preview_screens/detect%20(2).png)

![website_folders](https://github.com/Kamelleon/ObjectDetector/blob/main/preview_screens/detect%20(3).png)

![website_images](https://github.com/Kamelleon/ObjectDetector/blob/main/preview_screens/detect%20(4).png)
