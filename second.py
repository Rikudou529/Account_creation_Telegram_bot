import os
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
from telegram.error import BadRequest  # Import for error handling
from telethon import TelegramClient, events

logging.basicConfig(level=logging.INFO)

# Function to load excluded users from a text file
def load_excluded_users(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return set(line.strip() for line in file.readlines())
    return set()

# Dictionary to store message metadata (to track forwarded messages)
message_store = {}

class TelegramBotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Bot Control")

        self.bot_thread = None
        self.running = False
        self.app = None
        self.loop = None
        self.admin_ids = []
        self.token_value = []
        self.bot_name = []
        self.cnt = 0
        self.message_mapping = {}
        self.session_dir=""
        self.message_mapping = {}
        self.api_id = '1149742'  # Replace with your API ID
        self.api_hash = '51fcee2d03ef60ba96766c19a8e8b13b'  # Replace with your API hash
        self.session_files=[]
        self.tuple_list=[]
        self.session_vars = {}
        # Create widgets
        self.create_widgets()

    def load_token_files(self, file_path):
        admin_ids = ""
        token_values = ""
        bot_name = ""
        with open(file_path, "r", encoding='utf-8') as file:
            for line in file.readlines():
                if line.find("admin_chat_id") == 0:
                    admin_ids = line.split("admin_chat_id =")[-1].strip()
                    temp = admin_ids.split(",")
                    for i in temp:
                        self.admin_ids.append(i)
                if line.find("bot_token =") == 0:
                    token_values = line.split("bot_token =")[-1].strip()
                    temp = token_values.split(",")
                    for i in temp:
                        self.token_value.append(i)
                if line.find("bot_username =") == 0:
                    bot_name = line.split("bot_username =")[-1].strip()
                    temp = bot_name.split(",")
                    for i in temp:
                        self.bot_name.append(i)

    def create_widgets(self):
        self.load_token_files("settings.ini")
        
        # Create tabs
        tab_control = ttk.Notebook(self.root)

        # Create "Bot Control" tab
        tab1 = ttk.Frame(tab_control)
        tab_control.add(tab1, text="Bot Control")

        # Create "Session Management" tab
        tab2 = ttk.Frame(tab_control)
        tab_control.add(tab2, text="Session Management")

        tab_control.pack(expand=1, fill="both")

        # Bot Control tab components
        tk.Label(tab1, text="Admin Chat ID:").grid(row=0, column=0, padx=5, pady=5)
        self.admin_chat_id = ttk.Combobox(tab1)
        self.admin_chat_id['values'] = [index.strip() for index in self.admin_ids]
        self.admin_chat_id.current(0)  # Default option
        self.admin_chat_id.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(tab1, text="Bot Token:").grid(row=1, column=0, padx=5, pady=5)
        self.bot_token = ttk.Combobox(tab1)
        self.bot_token['values'] = [index.strip() for index in self.token_value]
        self.bot_token.current(0)  # Default option
        self.bot_token.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(tab1, text="User's File:").grid(row=2, column=0, padx=5, pady=5)
        self.users_file = tk.Entry(tab1)
        self.users_file.grid(row=2, column=1, padx=5, pady=5)
        tk.Button(tab1, text="Browse", command=self.browse_file).grid(row=2, column=2, padx=5, pady=5)

        self.run_button = tk.Button(tab1, text="Run", command=self.run_bot, width=20, height=5)
        self.run_button.grid(row=3, column=1, padx=5, pady=5)

        self.status_label = tk.Label(tab1, text="Status: Stopped")
        self.status_label.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        tk.Label(tab2, text="Session Directory:").grid(row=0, column=0, padx=5, pady=5)
        self.session_directory = tk.Entry(tab2)
        self.session_directory.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(tab2, text="Browse", command=self.browse_session_directory).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(tab2, text="Bot Name:").grid(row=1, column=0, padx=5, pady=5)
        self.bot_names = ttk.Combobox(tab2)
        self.bot_names['values'] = [index.strip() for index in self.bot_name]
        self.bot_names.current(0)  # Default option
        self.bot_names.grid(row=1, column=1, padx=5, pady=5)

        self.load_sessions_button = tk.Button(tab2, text="Load Sessions", command=self.load_sessions)
        self.load_sessions_button.grid(row=2, column=1, padx=5, pady=5)

        # Add "Select All" checkbox
        self.select_all_var = tk.BooleanVar()
        self.select_all_check = tk.Checkbutton(tab2, text="Select All", variable=self.select_all_var, command=self.select_all)
        self.select_all_check.grid(row=3, column=0, sticky="w")

        # Scrollable area for checkboxes
        self.canvas = tk.Canvas(tab2)
        self.canvas.grid(row=4, column=0, columnspan=3, padx=15, pady=15, sticky="nsew")

        self.scrollbar = tk.Scrollbar(tab2, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=4, column=3, sticky='ns')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.sessions_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.sessions_frame, anchor="nw")

        # Bind scrolling events to the canvas
        self.sessions_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Start button
        self.load_sessions_button = tk.Button(tab2, text="Start", command=self.temp_run)
        self.load_sessions_button.grid(row=5, column=5, padx=5, pady=5)


    def select_all(self):
        # Set all session checkboxes to the same state as the "Select All" checkbox
        for var in self.session_vars.values():
            var.set(self.select_all_var.get())

    def browse_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.users_file.delete(0, tk.END)
            self.users_file.insert(0, filename)

    def browse_session_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.session_directory.delete(0, tk.END)
            self.session_directory.insert(0, directory)

    def load_sessions(self):
        self.session_dir = self.session_directory.get()
        if not os.path.exists(self.session_dir):
            messagebox.showerror("Error", "Invalid session directory!")
            return

        for widget in self.sessions_frame.winfo_children():
            widget.destroy()  # Clear previous session checkboxes

        self.session_files = [f for f in os.listdir(self.session_dir) if f.endswith('.session')]

        if not self.session_files:
            messagebox.showinfo("Info", "No session files found!")
            return

        for session_file in self.session_files:
            var = tk.BooleanVar()
            self.session_vars[session_file] = var
            check = tk.Checkbutton(self.sessions_frame, text=session_file, variable=var)
            check.pack(anchor='w')

    def add_selected_to_tuple_list(self):
        """Add selected session file names to the tuple_list."""
        self.tuple_list.clear()  # Clear the list before adding new selections
        for session_file, var in self.session_vars.items():
            if var.get():  # Check if the checkbox is selected
                self.tuple_list.append(session_file)        

    def run_bot(self):
        if not self.admin_chat_id.get() or not self.bot_token.get() or not self.users_file.get():
            messagebox.showerror("Error", "All fields are required!")
            return

        self.status_label.config(text="Status: Running")
        self.bot_thread = threading.Thread(target=self.start_bot)
        self.bot_thread.start()
    def temp_run(self):
        self.second_bot = threading.Thread(target=self.second_start)
        self.second_bot.start()
    def second_start(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        api_id = '1149742'  # Replace with your API ID
        api_hash = '51fcee2d03ef60ba96766c19a8e8b13b'  # Replace with your API hash
        bot_token = self.bot_token.get()
        bot_name = self.bot_names.get()
        # Initialize the bot
        bot = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)
        admin_acc = int(self.admin_chat_id.get())

        # Function to forward messages from session accounts to admin
        async def forward_message_to_admin(event, session_name):
            if event.is_private:
                sender = await event.get_sender()
                sender_name = sender.username
                message_text = event.message.text
            
                # Forward message to admin account with info about the session and sender
                if sender_name:
                    self.message_mapping[event.id] = (event.sender_id, session_name)
                    await bot.send_message(admin_acc, f"Message from @{sender_name} (Session: {session_name}):\n\n{message_text}")

        # Function to handle reply from the admin account and send it back via the correct session
        async def handle_admin_reply(event):
            if event.is_private and event.sender_id == admin_acc:
                # Extract the message you replied to
                reply = await event.get_reply_message()
                if reply is None:
                    # logging.error("No reply message found.")
                    return
                if (reply.id) in self.message_mapping:
                    sender_id, session_name = self.message_mapping[reply.id]
                    session_client = session_clients.get(session_name)
                    
                    # Send the admin's reply to the original sender via the correct session
                    await session_client.send_message(sender_id, event.message.text)

        # Event handler to monitor private messages sent to session accounts
        @bot.on(events.NewMessage(pattern='/start'))
        async def handle_new_message(event):
            if event.is_private:
                session_name = event.client.session.filename
                await forward_message_to_admin(event, session_name)

        # Event handler to listen to replies from the admin account
        @bot.on(events.NewMessage(incoming=True, from_users=admin_acc))
        async def handle_admin_reply_event(event):
            await handle_admin_reply(event)

        # Session Management
        def create_client(session_file, api_id, api_hash):
            # Load session files dynamically based on the filenames
            return TelegramClient(session_file, api_id, api_hash)
        session_clients = {}

        # Function to start the bot for each session and click "start"
        async def start_bot_in_all_sessions():
            self.add_selected_to_tuple_list()
            for session_file in self.tuple_list:
                session_name = os.path.basename(session_file).replace('.session', '')
                
                # Skip bot_session (the bot itself)
                if session_name == 'bot_session':
                    continue
                
                client = create_client(self.session_dir+"/"+session_file, api_id, api_hash)
                session_clients[session_name] = client
                await client.start()
                print(f"Started session for {session_name}")
                
                # Send the start command to the bot in each session
                await client.send_message(bot_name, '/start')
                
                # Monitor messages in each session
                @client.on(events.NewMessage())
                async def session_message_handler(event):
                    await forward_message_to_admin(event, session_name)

        # Run the software
        async def main():
            await start_bot_in_all_sessions()
            await bot.run_until_disconnected()

        # Running everything
        loop.run_until_complete(main())
        loop.close()


    def start_bot(self):
        self.running = True

        # Get parameters from the UI
        bot_token = self.bot_token.get()
        admin_chat_id = int(self.admin_chat_id.get())
        excluded_users = load_excluded_users(self.users_file.get())

        # Define the message forwarding function (from group to private chat)
        async def forward_message(update: Update, context: CallbackContext):
            self.cnt = self.cnt+1
            user = update.message.from_user
            chat_type = update.message.chat.type
            chat_title = update.message.chat.title if update.message.chat.title else "Private Chat"
            message_id = update.message.message_id
            if user.username not in excluded_users:
                message = f"<b>Type:</b> {chat_type.capitalize()}\n"
                message += f"<b>Group/Channel:</b> {chat_title}\n"
                message += f"<b>User:</b> {user.full_name} (@{user.username})\n"
                message += f"<b>Message:</b> {update.message.text}"
                
                forwarded_msg = await context.bot.send_message(
                    chat_id=admin_chat_id, 
                    text=message, 
                    parse_mode="HTML"
                )

                # Store the original message information for reply tracking
                message_store[forwarded_msg.message_id] = {
                    'chat_id': update.message.chat_id,
                    'message_id': message_id
                }
 
        # Function to reply to the original group from the private chat
        async def reply_to_group(update: Update, context: CallbackContext):
            reply_message = update.message.text
            original_message_info = message_store.get(update.message.reply_to_message.message_id)

            if original_message_info:
                chat_id = original_message_info['chat_id']
                message_id = original_message_info['message_id']

                try:
                    forward1 = await context.bot.send_message(chat_id=chat_id, text=reply_message, reply_to_message_id=message_id)
                    # Log successful reply
                    logging.info(f"Reply sent successfully to chat_id: {chat_id}, message_id: {message_id}")
                    message_store[forward1.message_id] = {
                        'chat_id': update.message.chat_id,
                        'message_id': update.message.message_id
                    }
                except BadRequest as e:
                    logging.error(f"Failed to reply: {e}")

        # Function to handle replies to the bot's own messages in the group

        async def handle_reply_in_group(update: Update, context: CallbackContext):
            reply_message = update.message.text
            original_message_info = message_store.get(update.message.reply_to_message.message_id)
            if original_message_info:
                chat_id = original_message_info['chat_id']
                message_id = original_message_info['message_id']

                try:
                    forward2 = await context.bot.send_message(chat_id=chat_id, text=reply_message, reply_to_message_id=message_id)
                    # Log successful reply
                    message_store[forward2.message_id] = {
                        'chat_id': update.message.chat_id,
                        'message_id': update.message.message_id
                    }
                    logging.info(f"Reply sent successfully to chat_id: {chat_id}, message_id: {message_id}")
                except BadRequest as e:
                    logging.error(f"Failed to reply in group: {e}")
            else:
                user = update.message.from_user
                chat_type = update.message.chat.type
                chat_title = update.message.chat.title if update.message.chat.title else "Private Chat"
                message_id = update.message.message_id
                if user.username not in excluded_users:
                    message = f"<b>Type:</b> {chat_type.capitalize()}\n"
                    message += f"<b>Group/Channel:</b> {chat_title}\n"
                    message += f"<b>User:</b> {user.full_name} (@{user.username})\n"
                    message += f"<b>Message:</b> {update.message.text}"
                    
                    forwarded_msg = await context.bot.send_message(
                        chat_id=admin_chat_id, 
                        text=message, 
                        parse_mode="HTML"
                    )

                    # Store the original message information for reply tracking
                    message_store[forwarded_msg.message_id] = {
                        'chat_id': update.message.chat_id,
                        'message_id': message_id
                    }


        # Create a new asyncio event loop in this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Initialize the bot with the token
        self.app = Application.builder().token(bot_token).build()

        # Add handlers for forwarding messages and replying
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.REPLY), forward_message))
        self.app.add_handler(MessageHandler(filters.REPLY & filters.Chat(int(self.admin_chat_id.get())), reply_to_group))
        self.app.add_handler(MessageHandler(filters.REPLY, handle_reply_in_group))  # Handle replies to the bot's own messages

        # Run the bot's event loop
        self.app.run_polling(poll_interval=1)
        self.loop.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramBotUI(root)
    root.mainloop()
