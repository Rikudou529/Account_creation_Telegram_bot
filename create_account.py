import subprocess
import time
import pycountry
import requests
import phonenumbers
import xml.etree.ElementTree as ET
import logging
import tkinter as tk
import threading
from tkinter import ttk

logging.basicConfig(level=logging.INFO)


class TelegramBotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automatic")
        self.country_names = []
        self.api_key = ""
        self.create_widgets()

    def load_country(self,file_path):
        with open(file_path, "r", encoding='utf-8') as file:
            for line in file.readlines():
                country_name = line.strip()
                self.country_names.append(country_name)

    def create_widgets(self):

        self.load_country("country.txt")
        tk.Label(self.root, text="Select country:").grid(row=0, column=0, padx=5, pady=5)
        self.country_name_item = ttk.Combobox(self.root)
        self.country_name_item['values'] = [index.strip() for index in self.country_names]
        self.country_name_item.current(0)  # Index of the default option (0-based)
        self.country_name_item.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.root,text="Input the Api key:").grid(row=1,column=0,padx=5,pady=5)
        self.api_key_item = tk.Entry(self.root,width=20)
        self.api_key_item.grid(row=1,column=1,padx=5,pady=5)

        tk.Label(self.root,text="Input the count:").grid(row=2,column=0,padx=5,pady=5)
        self.account_num_item = tk.Entry(self.root, width=5)
        self.account_num_item.grid(row=2,column=1,padx=5,pady=5)

        tk.Label(self.root,text="Add the country:").grid(row=3,column=0,padx=5,pady=5)
        self.add_country_item = tk.Entry(self.root,width=10)
        self.add_country_item.grid(row=3,column=1,padx=5,pady=5)

        self.add_buton = tk.Button(self.root, text="Add", command=self.add_country, width=8, height=3)
        self.add_buton.grid(row=3, column=2, padx=5, pady=5)

        self.run_button = tk.Button(self.root,text="Run",command=self.run,width=10,height=5)
        self.run_button.grid(row=4,column=1,padx=5,pady=5)

    def add_country(self):
        country = self.add_country_item.get()
        temp = ""
        with open("country.txt", "r", encoding='utf-8') as file:
            temp = file.read()
            temp = temp + country + "\n"
        with open("country.txt","w",encoding='utf-8') as file:
            file.write(temp)
    
    def press_add_account_button(self,device="127.0.0.1:5555"):
        self.tap_screen(70,70,device="127.0.0.1:5555")
        self.dump_window_hierarchy(device)
        resource_id = 'org.thunderdog.challegram:id/btn_addAccount'
        bounds = self.find_element_bounds("window_dump.xml", resource_id)

        if bounds:
            self.tap_on_element(bounds, device)
            return 0
        else:
            resource_id="org.thunderdog.challegram:id/account"
            bounds = self.find_element_bounds("window_dump.xml", resource_id)
            if not bounds:
                self.tap_screen(100,250,device="127.0.0.1:5555")
                self.dump_window_hierarchy(device)
                resource_id="org.thunderdog.challegram:id/account"
                bounds = self.find_element_bounds("window_dump.xml", resource_id)
                if not bounds:
                    return 1
                resource_id = 'org.thunderdog.challegram:id/btn_addAccount'
                bounds = self.find_element_bounds("window_dump.xml", resource_id)
                if bounds:
                    self.tap_on_element(bounds, device)
                    return 0
                else:
                    while not bounds:
                        self.scroll_down(device)
                        self.dump_window_hierarchy(device)
                        bounds = self.find_element_bounds("window_dump.xml", resource_id)
                    self.tap_on_element(bounds, device)
                    return 0
                    
            else:
                resource_id = "org.thunderdog.challegram:id/btn_addAccount"
                bounds = self.find_element_bounds("window_dump.xml", resource_id)
                while not bounds:
                    self.scroll_down(device)
                    self.dump_window_hierarchy(device)
                    bounds = self.find_element_bounds("window_dump.xml", resource_id)
                self.tap_on_element(bounds, device)
                return 0

            # self.tap_on_element(bounds, device)
            # self.dump_window_hierarchy(device)
            # resource_id = 'org.thunderdog.challegram:id/btn_addAccount'
            # # Step 2: Find the "Add Account" button by its text or resource-id
            # bounds = self.find_element_bounds("window_dump.xml", resource_id)
            # if bounds:
            #     self.tap_on_element(bounds, device)
            # else:
            #     print("Add Account button not found.")
            #     return 1

    def run_adb_command(self,command, device="127.0.0.1:5555"):
        """Function to run adb commands for a specific device using subprocess."""
        adb_command = f'adb -s {device} {command}'
        result = subprocess.run(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print(f"Success: {result.stdout}")
        else:
            print(f"Error: {result.stderr}")
        return result.stdout

    def connect_to_ldplayer(self):
        """Connect ADB to LDPlayer."""
        print("Connecting to LDPlayer...")
        self.run_adb_command("connect 127.0.0.1:5555", device="")

        devices = self.run_adb_command("devices", device="")
        print(f"ADB Devices: {devices}")
        if "127.0.0.1:5555" in devices:
            print("Successfully connected to LDPlayer on 127.0.0.1:5555.")
        else:
            print("Failed to connect to LDPlayer.")

    def launch_telegram_x(self,device="127.0.0.1:5555"):
        """Launch Telegram X app."""
        print("Launching Telegram X...")
        self.run_adb_command("shell monkey -p org.thunderdog.challegram -c android.intent.category.LAUNCHER 1", device)

    def tap_screen(self,x, y, device="127.0.0.1:5555"):
        """Simulate a tap at the specified coordinates."""
        print(f"Tapping on coordinates ({x}, {y})...")
        self.run_adb_command(f"shell input tap {x} {y}", device)

    def input_text(self,text, device="127.0.0.1:5555"):
        """Input text (like phone number or verification code)."""
        print(f"Entering text: {text}...")
        self.run_adb_command(f'shell input text "{text}"', device)

    def press_enter(self,device="127.0.0.1:5555"):
        """Simulate pressing the Enter key."""

        print("Pressing Enter...")
        self.run_adb_command("shell input keyevent 66", device)

    def fetch_verification_code(self, request_number_url, max_retries=5):
        """Fetch verification code with retries on failure."""
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(request_number_url)
                number_data = response.json()
                if number_data['msg'] == "error":
                    print(f"Error fetching code, retrying... ({retries + 1}/{max_retries})")
                    retries += 1
                    resource_id="org.thunderdog.challegram:id/btn_forgotPassword"
                    bounds = self.find_element_bounds("window_dump.xml", resource_id)
                    if bounds:
                        self.tap_on_element(bounds, device="127.0.0.1:5555")
                    time.sleep(5)  # Small delay before retrying
                else:
                    return number_data['result']['code']  # Return the verification code
            except Exception as e:
                print("error:"+str(e))
                break
        
        print("Failed to fetch verification code after retries.")
        return None

    def clear_input_field(self, device="127.0.0.1:5555", repeat=10):
        """Simulate pressing the backspace key multiple times to clear the input field."""
        print("Clearing input field...")
        for _ in range(repeat):
            self.run_adb_command(f"shell input keyevent 67", device)  # Keyevent 67 is the backspace key

    def add_new_account(self,country_name,phone_number, hash_code, device="127.0.0.1:5555"):
        """Automate adding a new account to Telegram X."""
        temp = self.press_add_account_button(device="127.0.0.1:5555")
        if temp == 1:
        # Step 2: Tap 'Start Messaging' button (replace x and y with actual coordinates)
            resource_id="org.thunderdog.challegram:id/btn_done"
            bounds = self.find_element_bounds("window_dump.xml", resource_id)
            if bounds:
                self.tap_on_element(bounds, device)
        self.dump_window_hierarchy(device)
        resource_id="org.thunderdog.challegram:id/login_country"
        bounds = self.find_element_bounds("window_dump.xml", resource_id)
        if bounds:
            self.tap_on_element(bounds, device)
        self.input_text(country_name, device)
        resource_id = 'org.thunderdog.challegram:id/login_phone'
        bounds = self.find_element_bounds("window_dump.xml", resource_id)

        if bounds:
            self.tap_on_element(bounds, device)
        # self.clear_input_field(device, repeat=10)
        # time.sleep(6)
        self.input_text(phone_number, device)

        self.press_enter(device)
        request_number_url = f"https://api.fast-tg.org?apiKay={self.api_key}&action=getCode&hash_code={hash_code}"
        verification_code = self.fetch_verification_code(request_number_url, max_retries=5)
        if verification_code:
            self.input_text(verification_code, device)

            self.press_enter(device)
            self.press_enter(device)
            # self.press_enter(device)
            # self.run_adb_command("shell input keyevent KEYCODE_TAB", device)
            # self.press_enter(device)
        
        else:
            self.tap_screen(70,70,device="127.0.0.1:5555")
            self.dump_window_hierarchy(device)
            resource_id = 'org.thunderdog.challegram:id/login_phone'
            bounds = self.find_element_bounds("window_dump.xml", resource_id)

            if bounds:
                self.tap_on_element(bounds, device)
            self.clear_input_field(device, repeat=10)
            time.sleep(3)
            self.tap_screen(70,70,device="127.0.0.1:5555")

    def dump_window_hierarchy(self,device="127.0.0.1:5555"):
        """Dump the current UI hierarchy to a window_dump.xml file."""

        self.run_adb_command("shell uiautomator dump /sdcard/window_dump.xml", device)
        self.run_adb_command("pull /sdcard/window_dump.xml", device)

    def find_element_bounds(self,xml_file, resource_id=None):
        """Find the bounds of an element based on its resource-id."""

        tree = ET.parse(xml_file)
        root = tree.getroot()

        for node in root.iter('node'):
            node_id = node.attrib.get('resource-id')
            bounds = node.attrib.get('bounds')

            # Find the element with the matching resource-id
            if resource_id and resource_id == node_id:
                print(f"Found element with resource-id: {node_id}, bounds: {bounds}")
                return bounds
        return None

    def parse_bounds(self,bounds):
        """Parse the bounds string into coordinates."""

        bounds = bounds.strip('[]').split('][')
        left_top = list(map(int, bounds[0].split(',')))
        right_bottom = list(map(int, bounds[1].split(',')))
        return left_top, right_bottom

    def scroll_down(self,device="127.0.0.1:5555"):
        """Simulate scrolling down on the screen."""
        # Coordinates for scrolling: swipe from the bottom to the top of the screen
        print("Scrolling down...")
        self.run_adb_command(f"shell input swipe 100 900 100 300", device)
        time.sleep(5)  # Wait for the screen to settle after the scroll

    def tap_on_element(self,bounds, device="127.0.0.1:5555"):
        """Tap on the center of an element's bounds."""

        left_top, right_bottom = self.parse_bounds(bounds)
        x_center = (left_top[0] + right_bottom[0]) // 2
        y_center = (left_top[1] + right_bottom[1]) // 2
        self.tap_screen(x_center, y_center, device)

    def run(self):
        self.account = threading.Thread(target=self.start)
        self.account.start()
    def start(self):
        self.api_key = self.api_key_item.get()
        self.connect_to_ldplayer()
        country_name = self.country_name_item.get()
        number_count = int(self.account_num_item.get())
        country_code = pycountry.countries.lookup(country_name).alpha_2
        country_dial = phonenumbers.country_code_for_region(country_code)

        self.launch_telegram_x(device="127.0.0.1:5555")
        # self.add_new_account(country_name,"1233","dsfsdfsdf", device="127.0.0.1:5555")
        # self.add_new_account(country_name,"1234567","23de234dfe", device="127.0.0.1:5555")
        while number_count>0:
            request_number_url = f"https://api.fast-tg.org?apiKay={self.api_key}&action=getNumber&country={country_code}"
            response = requests.get(request_number_url)
            number_data = response.json()

            flag = number_data['error']
            if flag == "INFORMATION_SUCCESS":
                phone_number = number_data['result']['phone']
                phone_number = str(phone_number).replace(str(country_dial),"",1)
                hash_code = number_data['result']['hash_code']

                self.add_new_account(country_name,phone_number,hash_code, device="127.0.0.1:5555")
            else:
                print("error:"+flag)
            number_count = number_count-1

if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramBotUI(root)
    root.mainloop()
