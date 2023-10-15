import customtkinter as ctk
from telethon import TelegramClient, events
from telethon.tl.types import User
import sys
import threading
import asyncio
import queue


class OutputRedirector:
    def __init__(self, output_widget):
        self.output_widget = output_widget

    def write(self, string):
        self.output_widget.insert(ctk.END, string)

    def flush(self):
        pass

class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()

        self.title("Telegram Bot")
        self.geometry("500x500")
        self.channel_ids = []
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(side="left", fill="both", expand=True)
        
        self.create_widgets()
    def outputs(self):
        api_id = self.api_id.get()
        api_hash = self.api_hash.get()
        api_name = self.api_name.get()
        phone_number = self.number.get()
        self.output.insert(ctk.END, "------------------------\n")
        self.output.insert(ctk.END, "API ID: " + api_id + "\n")
        self.output.insert(ctk.END, "API Hash: " + api_hash + "\n")
        self.output.insert(ctk.END, "API Name: " + api_name + "\n")
        self.output.insert(ctk.END, "Phone Number: " + phone_number + "\n")
        self.output.insert(ctk.END, "Channel IDs: " + ', '.join(self.channel_ids) + "\n")
        self.output.insert(ctk.END, "------------------------\n")
        self.output.insert(ctk.END, "Bot started\n")
        self.output.insert(ctk.END, "------------------------\n")
    async def get_entity_id(self, client, entity): # Get the ID of the entity
            if entity.startswith('@'):  # It's a username
                entity = await client.get_entity(entity) # Get the entity from the username
                return entity.id # Return the ID of the entity
            else:  # It's an ID already
                return int(entity) # R
        
    def start(self):
        sys.stdout = OutputRedirector(self.output)
        self.output.delete('1.0', ctk.END) 
        self.outputs()
        api_id = self.api_id.get()
        api_hash = self.api_hash.get()
        api_name = self.api_name.get()
        phone_number = self.number.get()
        channel_ids = self.channel_ids
        sys.stdout = OutputRedirector(self.output)
        threading.Thread(target=self.run_telegram_client, args=(api_name, api_id, api_hash, phone_number, channel_ids, self.queue)).start()
        self.after(100, self.check_queue)
            
    def run_telegram_client(self, api_name, api_id, api_hash, phone_number, channel_ids, queue):
        async def get_code():
            print("get_code called")
            queue.put('get_code')
            while queue.empty() or queue.queue[0] == 'get_code':  # Wait until there is an item in the queue and it's not 'get_code'
                await asyncio.sleep(0.1)
            code = queue.get()
            print(f"Code received in get_code: {code}")  # Print the code received
            return code
        asyncio.set_event_loop(asyncio.new_event_loop())
        client = TelegramClient(api_name, api_id, api_hash)
        print("Before client.start")
        client.start(phone_number, code_callback=get_code)
        print("After client.start")

        
        
        print('Started Telegram Bot')
        print('Channels: ' + ', '.join(channel_ids))
        input_channel_ids = []
        for entity in channel_ids:
            id = client.loop.run_until_complete(self.get_entity_id(client, entity))
            input_channel_ids.append(id)
        print(f'Input channels: {input_channel_ids}')
        @client.on(events.NewMessage(chats=input_channel_ids)) # Listen to new messages in the channels
        async def handler(event):
            print(f'New message from {event.sender_id}: {event.message}')
            if event.message == 'ping':
                await event.reply('pong')
            elif event.message == 'pong':
                await event.reply('ping')
            elif event.message == 'Hey!':
                await event.reply('Hey!')
        print("Before client.run_until_disconnected")
        client.run_until_disconnected() # Start the client until Ctrl+C is pressed
        print("After client.run_until_disconnected")
        print("Telegram client started and waiting for events.")
    def check_queue(self):
        try:
            msg = self.queue.get(0)
            if msg == 'get_code':
                dialog = ctk.CTkInputDialog(text="Enter the code you received:", title="Telegram Code")
                code = dialog.get_input()
                print(f"Code entered in check_queue: {code}")  # Print the code entered
                if 'get_code' in self.queue.queue:  # Only put the code into the queue if 'get_code' is in the queue
                    self.queue.put(code)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_queue)
    def clear_input(self, event, entry, default_text):
        if entry.get() == default_text:
            entry.delete(0, "end")

    def lock_inputs(self):
        self.api_id.configure(state='disabled')
        self.api_hash.configure(state='disabled')
        self.api_name.configure(state='disabled')
        self.number.configure(state='disabled')

    def unlock_inputs(self):
        self.output.delete('1.0', ctk.END)  
        self.output.insert(ctk.END, "------------------------\n")
        self.output.insert(ctk.END, "Bot stopped\n")
        self.output.insert(ctk.END, "------------------------\n")
        self.api_id.configure(state='normal')
        self.api_hash.configure(state='normal')
        self.api_name.configure(state='normal')
        self.number.configure(state='normal')
        self.toggle_button.configure(text="Start", command=self.toggle_button_command)


    def create_button(self, text, command, parent=None):
        button = ctk.CTkButton(parent if parent is not None else self, text=text, command=command)
        button.pack(side="top", padx=5, pady=5)
        return button

    def create_input(self, text):
        label = ctk.CTkLabel(self, text=text)
        label.pack(side="top")
        entry = ctk.CTkEntry(self)
        default_text = "Enter your " + text
        entry.insert(0, default_text)
        entry.bind("<FocusIn>", lambda event: self.clear_input(event, entry, default_text))
        entry.pack(side="top")
        return entry

    def toggle_button_command(self):
        if self.toggle_button.cget("text") == "Start":
            self.start()
        else:
            self.unlock_inputs()

    def create_textbox(self, text, width_percent=50):  # Set the width_percent parameter to your desired value
        label = ctk.CTkLabel(self, text=text)
        label.pack(side="top")

        # Get the window's width in pixels
        window_width = self.winfo_screenwidth()

        # Calculate the width of the textbox as a percentage of the window's width
        textbox_width = int(window_width * width_percent / 100)

        textbox = ctk.CTkTextbox(self, width=textbox_width)  # Pass the width parameter to the CTkTextbox constructor
        textbox.pack(side="top", padx=10, pady=10)  # Add padding
        return textbox

    def save_to_file(self):
        api_id = self.api_id.get()
        api_hash = self.api_hash.get()
        api_name = self.api_name.get()
        phone_number = self.number.get()
        
        data = {
            "api_id": api_id,
            "api_hash": api_hash,
            "api_name": api_name,
            "phone_number": phone_number,
            "channel_ids": self.channel_ids
        }

        config = ctk.CTkInputDialog(text="Config name:", title="Save config")
        config_name = config.get_input()
        if config_name is not None:
            with open(f'{config_name}.txt', 'w') as f:
                f.write(str(data))

            self.channel_id_listbox.insert(ctk.END, "Config saved successfully\n")
            self.channel_id_listbox.see(ctk.END)
    def remove_green_text(self):
    # Check if the window is still running
        if self.winfo_exists():
            # Remove the green text
            self.output.delete('end-2l', ctk.END)
    def create_widgets(self):
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(side="left", fill="both", expand=True)        

    def read_from_file(self):
        config = ctk.CTkInputDialog(text="Config name:", title="Load config")
        config_name = config.get_input()
        try:
            with open(f'{config_name}.txt', 'r') as f:
                data = f.read()

            data = eval(data)

            api_id = data["api_id"]
            api_hash = data["api_hash"]
            api_name = data["api_name"]
            phone_number = data["phone_number"]
            self.channel_ids = data["channel_ids"]

            self.api_id.delete(0, 'end')
            self.api_id.insert(0, api_id)
            self.api_hash.delete(0, 'end')
            self.api_hash.insert(0, api_hash)
            self.api_name.delete(0, 'end')
            self.api_name.insert(0, api_name)
            self.number.delete(0, 'end')
            self.number.insert(0, phone_number)

            # Update the listbox with the loaded channel IDs
            self.update_channel_id_listbox()
            self.channel_id_listbox.insert(ctk.END, "Config loaded successfully\n")
            self.channel_id_listbox.see(ctk.END)
        except FileNotFoundError:
            print("No config file found")
    def add_channel_id(self):
        dialog = ctk.CTkInputDialog(text="Channel ID:", title="Add Channel ID")
        channel_id = dialog.get_input()
        if channel_id is not None:
            self.channel_ids.append(channel_id)
            self.update_channel_id_listbox()  # Update the listbox
    def update_channel_id_listbox(self):
        # Clear the listbox
        self.channel_id_listbox.delete('1.0', ctk.END)

        # Populate the listbox with channel IDs
        for channel_id in self.channel_ids:
            self.channel_id_listbox.insert(ctk.END, channel_id + "\n")
    def create_widgets(self):
        self.api_id = self.create_input("API ID")
        self.api_hash = self.create_input("API Hash")
        self.api_name = self.create_input("API Name")
        self.number = self.create_input("Phone Number")
        
        self.options = ["Add Channel ID", "Save", "Load"]
        self.selected_option = ctk.StringVar(value="Options")  # set the default option
        # Create a listbox for channel IDs
        
        self.channel_id_label = ctk.CTkLabel(self.button_frame, text="Channel IDs")

        self.channel_id_listbox = ctk.CTkTextbox(self.button_frame)
        self.channel_id_listbox.pack(side="bottom", padx=10, pady=10)

        # Populate the listbox with channel IDs
        for channel_id in self.channel_ids:
            self.channel_id_listbox.insert(ctk.END, channel_id)
        


        self.output = self.create_textbox("Bot Output", width_percent=15)
        self.output.pack(side="bottom")
        self.option_menu_label = ctk.CTkLabel(self.button_frame, text="Options")
        self.option_menu_label.pack(side="top", padx=5, pady=5)
        self.toggle_button = self.create_button("Start", self.start, self.button_frame)
        self.toggle_button.pack(side="top", padx=5, pady=5)

        self.option_menu = ctk.CTkOptionMenu(self.button_frame, values=self.options,
                                                command=self.handle_option,
                                                variable=self.selected_option)
        self.option_menu.pack(side="top", padx=5, pady=5)
    def handle_option(self, option):
        if option == "Add Channel ID":
            self.add_channel_id()
        elif option == "Save":
            self.save_to_file()
        elif option == "Load":
            self.read_from_file()
root = ctk.CTk()
app = GUI()
app.mainloop()