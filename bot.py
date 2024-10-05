import os
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
from telegram.error import BadRequest  # Import for error handling

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
        self.cnt=0
        # Create widgets
        self.create_widgets()
    
    def load_token_files(self, file_path):
        admin_ids = ""
        token_values = ""
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

    def create_widgets(self):
        self.load_token_files("settings.ini")
        # Admin Chat ID
        tk.Label(self.root, text="Admin Chat ID:").grid(row=0, column=0, padx=5, pady=5)
        self.admin_chat_id = ttk.Combobox(self.root)
        self.admin_chat_id['values'] = [index.strip() for index in self.admin_ids]
        self.admin_chat_id.current(0)  # Index of the default option (0-based)
        self.admin_chat_id.grid(row=0, column=1, padx=5, pady=5)

        # Bot Token
        tk.Label(self.root, text="Bot Token:").grid(row=1, column=0, padx=5, pady=5)
        self.bot_token = ttk.Combobox(self.root)
        self.bot_token['values'] = [index.strip() for index in self.token_value]
        self.bot_token.current(0)  # Index of the default option (0-based)
        self.bot_token.grid(row=1, column=1, padx=5, pady=5)

        # Excluded users file
        tk.Label(self.root, text="User's File:").grid(row=2, column=0, padx=5, pady=5)
        self.users_file = tk.Entry(self.root)
        self.users_file.grid(row=2, column=1, padx=5, pady=5)
        tk.Button(self.root, text="Browse", command=self.browse_file).grid(row=2, column=2, padx=5, pady=5)

        # Run and Stop buttons
        self.run_button = tk.Button(self.root, text="Run", command=self.run_bot, width=20, height=5)
        self.run_button.grid(row=3, column=1, padx=5, pady=5)

        # Status label
        self.status_label = tk.Label(self.root, text="Status: Stopped")
        self.status_label.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

    def browse_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.users_file.delete(0, tk.END)
            self.users_file.insert(0, filename)

    def run_bot(self):
        if not self.admin_chat_id.get() or not self.bot_token.get() or not self.users_file.get():
            messagebox.showerror("Error", "All fields are required!")
            return

        self.status_label.config(text="Status: Running")

        # Start the bot in a separate thread
        self.bot_thread = threading.Thread(target=self.start_bot)
        self.bot_thread.start()

    def stop_bot(self):
        if self.running and self.app:
            self.status_label.config(text="Status: Stopping...")
            self.app.stop()  # Stop the bot gracefully
            if self.loop:
                self.loop.stop()  # Stop the asyncio event loop

            if self.bot_thread and self.bot_thread.is_alive():
                self.bot_thread.join()  # Ensure the bot thread finishes

        self.status_label.config(text="Status: Stopped")
        self.run_button.config(state=tk.NORMAL)
        self.running = False

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
                # original_message_info = message_store.get(update.message.reply_to_message.message_id+self.cnt)
                # chat_id = original_message_info['chat_id']
                # message_id = original_message_info['message_id']

                # try:
                #     forward1 = await context.bot.send_message(chat_id=chat_id, text=reply_message, reply_to_message_id=message_id)
                #     # Log successful reply
                #     logging.info(f"Reply sent successfully to chat_id: {chat_id}, message_id: {message_id}")
                #     message_store[forward1.message_id] = {
                #         'chat_id': update.message.chat_id,
                #         'message_id': update.message.message_id
                #     }
                # except BadRequest as e:
                #     logging.error(f"Failed to reply: {e}")
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
