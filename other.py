from telethon import TelegramClient, events

# API credentials for the account (not your account)
api_id = '1149742'  # Replace with your API ID
api_hash = '51fcee2d03ef60ba96766c19a8e8b13b'  # Replace with your API hash
session_file = 'receiving_account.session'  # Session file for the receiving account

my_account_session = 'my_session'  # Your session file

# A account session file
a_account_session = 'receiving_account'  # Session file for Account A

# Initialize clients for both Account A and your account
a_client = TelegramClient(a_account_session, api_id, api_hash)
my_client = TelegramClient(my_account_session, api_id, api_hash)

# Dictionary to store forwarded message mappings
forwarded_message_map = {}

# Handle messages received by Account A
@a_client.on(events.NewMessage)
async def handle_message(event):
    sender = await event.get_sender()
    message = event.message
    # Forward the message to your account (Account C)
    forwarded_message = await my_client.send_message('me', f'Message from {sender.username}: {message.text}')
    
    # Map the forwarded message ID to the original message and sender
    forwarded_message_map[forwarded_message.id] = (event.message.id, event.chat_id)

# Handle replies sent from your account
@my_client.on(events.NewMessage(outgoing=True))
async def handle_reply(event):
    if event.reply_to_msg_id in forwarded_message_map:
        original_message_id, original_chat_id = forwarded_message_map[event.reply_to_msg_id]
        # Reply to the original sender from Account A
        await a_client.send_message(original_chat_id, event.message.text, reply_to=original_message_id)
        print(f'Replied to {original_chat_id} with: {event.message.text}')
    else:
        print("No corresponding message found in the map for this reply.")

# Start both clients
async def main():
    await a_client.start()
    await my_client.start()
    print("Clients started. Listening for messages...")
    await a_client.run_until_disconnected()
    await my_client.run_until_disconnected()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())