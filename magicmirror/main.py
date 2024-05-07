import tkinter as tk
from okviri.mqttp import MQTTHandler
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
import os

# Global image cache dictionary
image_cache_dict = {}

class MagicMirror(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Magic Mirror")
        self.geometry("600x800")
        self.configure(bg="#121212")
        self.create_widgets()

    def create_widgets(self):
        self.clock_label = tk.Label(self, text="", font=("Helvetica", 48), foreground="#FFFFFF", background="#121212")
        self.clock_label.grid(row=0, column=0, columnspan=2, pady=20)

        self.weather_icon = tk.Label(self, font=("Helvetica", 16), image=self.load_image("sunny.png"),
                                     compound=tk.TOP, foreground="#FFFFFF", background="#121212")
        self.weather_icon.image = self.load_image("sunny.png")
        self.weather_icon.grid(row=1, column=0, padx=10, pady=10)

        self.weather_label = tk.Label(self, text="Sunny", font=("Helvetica", 16), foreground="#FFFFFF",
                                      background="#121212")
        self.weather_label.grid(row=1, column=1, pady=10)

        self.temperature_label = tk.Label(self, text="", font=("Helvetica", 16), foreground="#FFFFFF",
                                          background="#121212")
        self.temperature_label.grid(row=2, column=0, pady=20)

        self.humidity_label = tk.Label(self, text="", font=("Helvetica", 16), foreground="#FFFFFF",
                                       background="#121212")
        self.humidity_label.grid(row=2, column=1, pady=20)

        # Create clothing labels dynamically based on the number of icons
        for i in range(3):
            clothing_label = tk.Label(self, background="#121212")
            clothing_label.grid(row=3, column=i, pady=20)
            setattr(self, f'clothing_label_{i}', clothing_label)

        self.date_label = tk.Label(self, text="Monday, January 1", font=("Helvetica", 18), foreground="#FFFFFF",
                                   background="#121212")
        self.date_label.grid(row=5, column=0, columnspan=2, pady=20)

        self.quotes_label = tk.Label(self, text="", font=("Helvetica", 14), foreground="#FFFFFF", background="#121212",
                                     wraplength=600)
        self.quotes_label.grid(row=6, column=0, columnspan=2, pady=20)

        self.update_quote()

    def update_quote(self):
        try:
            quote_data = self.get_random_quote()
            quote = f'"{quote_data["content"]}" - {quote_data["author"]}'
            self.quotes_label.config(text=quote)
        except Exception as e:
            print(f"Error: {e}")

        self.after(15000, self.update_quote)

    def get_random_quote(self):
        response = requests.get("https://api.quotable.io/random")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Status code: {response.status_code}")

    def update_clock(self):
        current_time = datetime.now().strftime("%H:%M")
        self.clock_label.config(text=current_time)
        self.after(1000, self.update_clock)

    def update_weather(self):
        temperature, humidity, conditions = self.fetch_weather_data()

        # Update weather-related labels and icons
        self.weather_label.config(image=self.load_image(conditions[0]))
        self.weather_label.image = self.load_image(conditions[0])
        self.temperature_label.config(text=f"Temperature: {temperature}°C")
        self.humidity_label.config(text=f"Humidity: {humidity}%")

        # Get weather and clothing icons based on temperature and conditions
        clothing_icons = self.get_clothing_icon_filename(float(temperature))
        weather_icons = self.get_weather_condition(float(temperature))

        # Update clothing labels with the appropriate icons
        for i in range(min(3, len(clothing_icons))):  # Display up to three clothing icons
            clothing_label = getattr(self, f'clothing_label_{i}')
            clothing_label.config(image=self.load_image(clothing_icons[i]))
            clothing_label.image = self.load_image(clothing_icons[i])

        # Update weather icon
        self.weather_icon.config(image=self.load_image(weather_icons[0]))
        self.weather_icon.image = self.load_image(weather_icons[0])

    def update_clothing(self):
        temperature, _, _ = self.fetch_weather_data()

        # Get clothing icons based on temperature
        clothing_icons = self.get_clothing_icon_filename(float(temperature))

        # Update clothing labels with the appropriate icons
        for i, icon in enumerate(clothing_icons):  # Display all clothing icons
            clothing_label = getattr(self, f'clothing_label_{i}')
            clothing_label.config(image=self.load_image(icon))
            clothing_label.image = self.load_image(icon)

        # Clear any remaining labels
        for i in range(len(clothing_icons), 3):
            clothing_label = getattr(self, f'clothing_label_{i}')
            clothing_label.config(image=None)
            clothing_label.image = None

    def fetch_weather_data(self):
        URL = "https://vrijeme.hr/hrvatska_n.xml"
        response = requests.get(URL)
        soup = BeautifulSoup(response.content, 'xml')

        for element in soup.find_all('GradIme'):
            if element.text == "Split-Marjan":
                grad = element.parent
                podatci = grad.find("Podatci")
                temp = podatci.find("Temp").text if podatci.find("Temp") is not None else "N/A"
                vlaga = podatci.find("Vlaga").text if podatci.find("Vlaga") is not None else "N/A"
                return temp, vlaga, self.get_weather_condition(float(temp))

        return "N/A", "N/A", ["Unknown"]

    def get_weather_condition(self, temperature):
        print(f"Temperature: {temperature}")
        try:
            temperature = float(temperature)
            if temperature > 25:
                return ("sunny.png",)
            elif 12 <= temperature <= 22:
                return ("suncloud.png",)
            elif 0 <= temperature < 12:
                return ("umbrella.png", "cloudrain.png")
            else:
                return ("snowman.png", "snowflake.png", "cloudflake.png")
        except ValueError as e:
            print(f"Error converting temperature to float: {e}")
            return ("unknown.png",)

    def get_clothing_icon_filename(self, temperature):
        if temperature > 22:
            return "shortsleeve.png", "sunglases.png"
        elif 12 <= temperature <= 22:
            return "coat.png"
        elif 0 <= temperature < 12:
            return "scarf.png", "gloves.png"
        elif temperature < 0:
            return "iceskate.png"
        else:
            return "question_mark.png"

    def update_date(self, date_str):
        self.date_label.config(text=date_str)

    def start_mirror(self):
        mqtt_handler = MQTTHandler(self)
        mqtt_handler.start()
        self.update_clock()
        self.update_date(datetime.now().strftime("%A, %B %d"))
        self.update_weather()
        self.update_clothing()  # Call the new function to update clothing
        self.mainloop()

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


if __name__ == "__main__":
    magic_mirror = MagicMirror()
    magic_mirror.start_mirror()
