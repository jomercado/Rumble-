import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os

intents = discord.Intents.default()
intents.message_content = True

TOKEN = os.getenv(MTM5NzgyNTE0MDk5NzM1NzU5OA.GlEdcH.y2yHiV847pDLiCjliuJ8wgCpHputxDRt_DmQVg)
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

MAX_PLAYERS = 100
players = []
game_started = False

# Load mock NFT data
with open("data/mock_nfts.json", "r") as f:
    nft_data = json.load(f)

class Player:
    def __init__(self, user, nft):
        self.user = user
        self.nft = nft
        self.hp = 100
        self.alive = True
        self.defending = False

def generate_mock_stats(nft):
    return {
        "name": nft["name"],
        "image": nft["image"],
        "overall_strength": nft.get("overall_strength", random.randint(60, 100)),
        "attack": nft.get("attack", random.randint(10, 20)),
        "defense": nft.get("defense", random.randint(5, 15)),
        "stamina": nft.get("stamina", random.randint(50, 100))
    }

@tree.command(name="rumble", description="Join the NFT Rumble!")
async def rumble(interaction: discord.Interaction):
    global game_started
    if game_started:
        await interaction.response.send_message("A game is already in progress!")
        return

    players.clear()
    game_started = True
    await interaction.response.send_message("🎮 **NFT Rumble starting!** React with 🔥 to join. Starting in 15 seconds...")

    msg = await interaction.original_response()
    await msg.add_reaction("🔥")

    await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=15))
    updated_msg = await interaction.channel.fetch_message(msg.id)
    users = [user async for user in updated_msg.reactions[0].users() if not user.bot]

    if len(users) < 2:
        await interaction.followup.send("❌ Not enough players joined.")
        game_started = False
        return

    for user in users[:MAX_PLAYERS]:
        nft = generate_mock_stats(random.choice(nft_data))
        players.append(Player(user, nft))

    await start_game(interaction.channel)

async def start_game(channel):
    round_num = 1
    while len([p for p in players if p.alive]) > 1:
        alive_players = [p for p in players if p.alive]
        attacker = random.choice(alive_players)
        target = random.choice([p for p in alive_players if p != attacker])

        damage = attacker.nft["attack"] - (target.nft["defense"] if target.defending else 0)
        damage = max(0, damage)
        target.hp -= damage
        target.defending = False

        if target.hp <= 0:
            target.alive = False
            await channel.send(f"💀 {target.user.mention} was defeated by {attacker.user.mention}!")
        else:
            await channel.send(
                embed=discord.Embed(
                    title=f"Round {round_num}",
                    description=f"⚔️ {attacker.user.mention} attacked {target.user.mention} for **{damage}** damage.",
                    color=discord.Color.red()
                ).set_thumbnail(url=attacker.nft["image"])
            )

        round_num += 1
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=3))

    winner = [p for p in players if p.alive][0]
    await channel.send(f"🏆 **{winner.user.mention} wins the NFT Rumble!**")

@bot.event
async def on_ready():
    try:
        synced = await tree.sync()
        print(f"Synced {{len(synced)}} slash commands")
    except Exception as e:
        print("Sync failed:", e)

    print(f"Bot is online as {{bot.user}}")

bot.run(TOKEN)
