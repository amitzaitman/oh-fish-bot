
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from game_logic import Game, Card, NUM_PLAYERS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Join Game", callback_data="join_game")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    context.bot_data['game'] = Game()
    context.bot_data['game'].group_chat_id = update.effective_chat.id
    
    await update.message.reply_text(
        f'Welcome to the Card Game Bot! Click the button below to join. We need {NUM_PLAYERS} players to start.',
        reply_markup=reply_markup
    )

async def join_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    game = context.bot_data.get('game')
    if not game or query.message.chat_id != game.group_chat_id:
        await query.edit_message_text('No active game or wrong chat. Start a game first.')
        return

    user = query.from_user
    username = user.username or f"Player_{user.id}"

    if game.add_player(user.id, username):
        await query.edit_message_text(
            f"{username} has joined the game! "
            f"{NUM_PLAYERS - len(game.players)} more player(s) needed."
        )
        
        keyboard = [[InlineKeyboardButton(str(i), callback_data=f"set_key_{i}") for i in range(1, 11)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=user.id,
            text="You've joined the game! Please select your encryption key (1-10):",
            reply_markup=reply_markup
        )

        if len(game.players) == NUM_PLAYERS:
            await context.bot.send_message(
                chat_id=game.group_chat_id,
                text="Game is full! All players should set their keys in the private chat with the bot. "
                     "The game will start automatically once all keys are set."
            )
    else:
        await query.edit_message_text("Unable to join the game. It might be full or you're already in.")

async def set_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    game = context.bot_data.get('game')
    if not game:
        await query.edit_message_text('No active game. Join a game first.')
        return

    user = query.from_user
    player = game.players.get(user.id)
    if not player or game.started:
        await query.edit_message_text("You're not in the game or the game has already started.")
        return

    key = int(query.data.split('_')[2])
    player.set_key(key)
    await query.edit_message_text(f"Your key has been set to {key}. Wait for the game to start in the group chat.")

    if game.all_keys_set():
        game.start_game()
        await send_hands(context)
        await send_game_status(context)

async def send_hands(context: ContextTypes.DEFAULT_TYPE):
    game = context.bot_data['game']
    for player in game.players.values():
        hand = player.get_decrypted_hand()
        formatted_hand = ', '.join([str(Card.from_string(card)) for card in hand])
        await context.bot.send_message(
            chat_id=player.user_id, 
            text=f"Your hand: {formatted_hand}\n"
                 f"Wait for your turn in the group chat."
        )

async def send_game_status(context: ContextTypes.DEFAULT_TYPE):
    game = context.bot_data['game']
    current_player = game.players[game.current_player]
    playable_cards = game.get_playable_cards()
    
    status = "🃏 Game Status 🃏\n\n"
    status += f"Current player: {current_player.username}\n\n"
    
    # Create a table for players
    status += "Players:\n"
    for player in game.players.values():
        icon = '👉' if player.user_id == game.current_player else '👤'
        turn_status = "(current turn)" if player.user_id == game.current_player else ""
        status += f"{icon} {player.username}: {len(player.hand)} cards {turn_status}\n"
    
    status += "\nCards on the table:\n"
    if game.table:
        for player_name, card in game.table:
            status += f"{player_name}: {card}\n"
    else:
        status += "No cards played yet.\n"
    
    status += f"\n{current_player.username}, it's your turn! Please select a card to play:"

    keyboard = [[InlineKeyboardButton(str(Card.from_string(card)), callback_data=f"play_{card}") for card in playable_cards]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=game.group_chat_id, text=status, reply_markup=reply_markup)

async def play_card_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    game = context.bot_data.get('game')
    if not game or not game.started:
        await query.edit_message_text(text="No active game or game hasn't started.")
        return

    user = query.from_user
    if user.id != game.current_player:
        await query.edit_message_text(text="It's not your turn. Please wait for your turn.")
        return

    card_to_play = query.data.split('_')[1]
    player = game.players[user.id]
    decrypted_hand = player.get_decrypted_hand()

    if card_to_play in decrypted_hand:
        encrypted_card = player.hand[decrypted_hand.index(card_to_play)]
        player.remove_card(encrypted_card)
        played_card = str(Card.from_string(card_to_play))
        
        game.play_card(player, played_card)
        
        await query.edit_message_text(text=f"{player.username} played {played_card}")

        game.next_player()
        await context.bot.send_message(
            chat_id=game.group_chat_id, 
            text=f"Moving to {game.players[game.current_player].username}'s turn..."
        )
        await send_game_status(context)
    else:
        await end_game(context, player)

async def end_game(context: ContextTypes.DEFAULT_TYPE, winner):
    game = context.bot_data['game']
    await context.bot.send_message(
        chat_id=game.group_chat_id,
        text=f"Game Over! {winner.username} wins!"
    )
    context.bot_data['game'] = None