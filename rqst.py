from py1337x import py1337x
from discord.ext import commands
import discord, qbittorrentapi, shutil, os, asyncio
from datetime import timedelta, datetime
from time import sleep

# Function to move .mp4 or .mkv files after download completes
def move_video_files(torrent_hash, destination_folder, ctx):
    # Get the torrent info
    torrent = qb.torrents_info(torrent_hashes=torrent_hash)[0]
    
    # Get the torrent's save path
    save_path = torrent.save_path

    # Flag to check if any video files were found
    video_files_found = False

    # Walk through the directory to find .mp4 or .mkv files
    for root, dirs, files in os.walk(save_path):
        for file in files:
            if file.endswith('.mp4') or file.endswith('.mkv'):
                video_files_found = True  # Set the flag to True
                file_path = os.path.join(root, file)
                try:
                    # Move the file to the destination folder
                    shutil.move(file_path, destination_folder)
                    print(f'Moved {file} to {destination_folder}')
                except Exception as e:
                    print(f'Error moving {file}: {e}')

    # Check if no video files were found
    if not video_files_found:
        print('No video files found in the torrent. Cannot add.')

    # Delete the torrent after moving the files
    delete_torrent(torrent_hash)


# Function to delete a torrent by its hash
def delete_torrent(torrent_hash):
    try:
        qb.torrents_delete(delete_files=True, torrent_hashes=torrent_hash)
        print(f'Torrent with hash {torrent_hash} has been deleted.')
    except Exception as e:
        print(f'Error deleting torrent with hash {torrent_hash}: {e}')


# Function to monitor torrent download completion
async def monitor_torrent(torrent_hash, destination_folder, ctx):
    while True:
        # Get the list of torrents
        torrents = qb.torrents_info(torrent_hashes=torrent_hash)
        
        if not torrents:
            print(f'No torrent found for hash: {torrent_hash}')
            break

        torrent = torrents[0]
        if torrent.state == 'pausedUP' or torrent.state == 'completed':
            print(f"Torrent {torrent.name} has completed downloading.")
            move_video_files(torrent_hash, destination_folder, ctx)
            break
        else:
            print(f'Torrent {torrent.name} is still downloading...')
        await asyncio.sleep(10)  # Use asyncio.sleep instead of time.sleep

# Function to add and monitor the torrent
async def add_and_monitor_torrent(magnet_link, destination_folder, ctx):
    # Add torrent and retrieve hash
    qb.torrents_add(urls=magnet_link)
    
    # Wait briefly to ensure the torrent appears in the list
    await asyncio.sleep(5)
    
    # Get the list of active torrents and sort by the 'added_on' field to find the most recent one
    torrents = qb.torrents_info(sort='added_on')
    
    if torrents:
        # Assume the most recently added torrent is the correct one
        most_recent_torrent = torrents[0]
        torrent_hash = most_recent_torrent.hash
        print(f"Monitoring torrent: {most_recent_torrent.name} with hash: {torrent_hash}")
        await monitor_torrent(torrent_hash, destination_folder, ctx)  # Call async function
    else:
        print('Torrent was not added successfully or not found.')


async def searchTorrent(query, ctx):
    results = torrents.search(query, category='movies', sortBy='size', order='desc')

    if not results['items']:
        await ctx.send('No torrents found for your query.')
        return  # Stop further execution if no torrents were found
    else:
        global found
        found = True

    names = [item['link'] for item in results['items']]
    english_torrents = []
    count = 0

    for link in names:
        english = torrents.info(link)
        if english['language'] == 'English':
            count += 1
            english_torrents.append(link)
        if count == 5:
            break

    if not english_torrents:
        await ctx.send('No English torrents were found.')
        return  # Stop further execution if no English torrents were found

    await downloadTorrent(english_torrents, ctx)  # Await the download function


async def downloadTorrent(english_torrents, ctx):
    if len(english_torrents) == 0:
        await ctx.send('No English torrents were found.')
        return  # Stop further execution if no torrents were found
    else:
        if int(torrents.info(english_torrents[0])['seeders']) <= int(min_seeders):
            await ctx.send(f'No English torrents above {min_seeders} seeders were found.')
            return  # Stop further execution if no torrents meet the seeder threshold
        else:
            magnet = torrents.info(english_torrents[0])['magnetLink']
            await ctx.send('Movie found, downloading...')
            # Add and monitor the torrent
            await add_and_monitor_torrent(magnet, destination_folder, ctx)  # Await the async function

# Start

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

description = "Request bot for Theater."
bot = commands.Bot(command_prefix='*', description=description, intents=intents)

try:
    with open('config.txt', 'r') as conf:
        TOKEN = conf.readline().strip()
        REQUEST_LIMIT = int(f.readline().strip())
        RESET_PERIOD = timedelta(hours=int(f.readline().strip()))
        quality = f.readline().strip()
        min_seeders = f.readline().strip()
        ALLOWED_CHANNEL_ID = int(f.readline().strip())
        destination_folder = f.readline().strip()
        qb_username = f.readline().strip()
        qb_password = f.readline().strip()
except FileNotFoundError:
    print("CONFIG.TXT NOT FOUND... CANNOT CONTINUE.")
    sleep(5)
    exit()
    
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


# Initialize request tracking variables
total_requests = 0
last_reset_time = datetime.now()

# Create a command to download movies
@bot.command(name='download')
async def download(ctx, *, movie_name: str):
    global total_requests, last_reset_time

    # Reset the total request count if the reset period has passed
    if datetime.now() - last_reset_time > RESET_PERIOD:
        total_requests = 0
        last_reset_time = datetime.now()

    # Check if the command is used in the allowed channel
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        return await ctx.send("You can't use this command in this channel.")
    
    # Check if the total requests have reached the limit
    if total_requests >= REQUEST_LIMIT:
        time_left = RESET_PERIOD - (datetime.now() - last_reset_time)
        await ctx.send(f"The request limit of {REQUEST_LIMIT} has been reached. Please wait {time_left.seconds // 3600} hours and {((time_left.seconds // 60) % 60)} minutes.")
        return

    # Prepare the search query
    search_query = f"{movie_name} {quality}"
    await ctx.send(f"Searching for torrents for: {search_query}")
    
    # Simulating the torrent search (replace with your actual search function)
    await searchTorrent(search_query, ctx)
    
    # Increment the total request count
    total_requests += 1
    if found:
        await ctx.send(f"Download complete for: {movie_name}")
        await ctx.send(f"$refresh")

# Variables
torrents = py1337x(proxy='1337x.to', cache='py1337xCache', cacheTime=0)
qb = qbittorrentapi.Client(host='http://154.53.44.231:8080', username=qb_username, password=qb_password)

connected = False
while not connected:
    try:
        qb.auth_log_in()
        connected = True
        print("Successfully connected to qBittorrent.")
    except qbittorrentapi.LoginFailed as e:
        print(f"qBittorrent login failed: {e}. Retrying in 10 seconds...")
    sleep(10)  # Wait for 10 seconds before retrying

bot.run(TOKEN)
