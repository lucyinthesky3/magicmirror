import paho.mqtt.client as mqtt
from threading import Thread
from time import sleep
from PIL import Image, ImageTk
import os

image_cache_dict = {}


class MQTTHandler(Thread):
    def __init__(self, magic_mirror):
        super().__init__()
        self.client = mqtt.Client("MagicMirrorSubscriber")
        self.client.on_message = self.on_message
        self.magic_mirror = magic_mirror

    def on_message(self, client, userdata, message):
        topic = message.topic
        payload = message.payload.decode("utf-8")
        print(f"Received message on topic '{topic}': {payload}")

        if topic == "TEMPERATURA":
            self.handle_temperature(payload)

    def handle_temperature(self, data):
        try:
            temp = float(data.split(" ")[1])
            weather_condition = self.get_weather_condition(temp)
            self.magic_mirror.update_weather(weather_condition)
        except ValueError:
            print("Invalid temperature value")

    def get_weather_condition(self, temperature):
        if temperature > 25:
            return "sunny.png"
        elif 12 <= temperature <= 22:
            return "suncloud.png"
        elif 0 <= temperature < 12:
            return "umbrella.png"
        else:
            return "snowman.png"

    def run(self):
        self.client.connect("localhost", 1883)
        self.client.loop_start()
        self.client.subscribe("TEMPERATURA")

        sleep(300)

        self.client.loop_stop()


    def load_image(self, filename):
        path = os.path.join("emoji_images", filename)
        print(f"Loading image: {path}")

        # Check if the image has already been loaded
        if path in image_cache_dict:
            return image_cache_dict[path]

        # Open the image with PIL
        img_pil = Image.open(path)

        # Convert the PIL image to a PhotoImage object
        img_tk = ImageTk.PhotoImage(img_pil)

        # Store the reference to avoid garbage collection
        image_cache_dict[path] = img_tk

        return img_tk

