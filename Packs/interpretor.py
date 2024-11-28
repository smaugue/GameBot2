# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import discord
import os
import re
from Packs.Botloader import Bot
import aiohttp
from gtts import gTTS
from datetime import datetime

class SendMessageAction:
    def __init__(self, content):
        self.content = content
    async def execute(self, ctx):
        await ctx.send(self.content)

class GenerateMP3Action:
    def __init__(self, text, lang='fr'):
        self.text = text
        self.lang = lang
    async def execute(self, ctx):
        startTime = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
        tts = gTTS(text=self.text, lang=self.lang)
        output_filename = f'{ctx.guild.id}_{startTime}_output.mp3'
        if os.path.exists(output_filename):
            i = 2
            while os.path.exists(f'{ctx.guild.id}_{startTime}_{i}_output.mp3'):
                i += 1
            output_filename = f'{ctx.guild.id}_{startTime}_{i}_output.mp3'  
        tts.save(output_filename)
        await ctx.send(file=discord.File(output_filename))
        os.remove(output_filename)

class CreateRoleAction:
    def __init__(self, name, color):
        self.name = name
        self.color = discord.Color(int(color, 16))
    async def execute(self, ctx):
        guild = ctx.guild
        await guild.create_role(name=self.name, color=self.color)
        await ctx.send(f"Role '{self.name}' created with color {self.color}.")

class SendImageFromURLAction:
    def __init__(self, url):
        self.url = url
    async def execute(self, ctx):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    if response.status == 200:
                        data = await response.read()
                        with open('temp_image.png', 'wb') as f:
                            f.write(data)
                        await ctx.send(file=discord.File('temp_image.png'))
                        os.remove('temp_image.png')
                    else:
                        await ctx.send('Failed to retrieve image from URL.')
        except Exception as e: Bot.console("WARN", f"Erreur:{e}")

def parse_actions(ctx, actions: str):
    action_list = []
    if actions is not None:
        actions = actions.strip()
    else: return action_list
    
    if '}&' in actions:
        action_strs = actions.split('}&')
    else:
        action_strs = [actions]

    def check_secondary(content: str):
        calc_matches = re.findall(r'Calc\[(.*?)\]', content)
        mention_matches = re.findall(r'@Mention', content)
        copy_matches = re.findall(r'Copy\[(.*?)\]', content)
        for calc_expression in calc_matches:
            try:
                result = eval(calc_expression)
                content = content.replace(f'Calc[{calc_expression}]', str(result))
            except Exception as e:
                Bot.console("WARN", f"Erreur lors de l'évaluation de {calc_expression}: {e}")
        for mention in mention_matches:
            try:
                content = content.replace(f'@Mention', ctx.author.mention)
            except Exception as e:
                Bot.console("WARN", f"Erreur: {e}")
        for copy in copy_matches:
            try:
                content = content.replace(f'Copy[{copy}]', f"```{copy}```")
            except Exception as e:
                Bot.console("WARN", f"Erreur: {e}")
        return content

    for action_str in action_strs:
        action_str = action_str + '}'
        send_message_match = re.match(r'SendMessage\{(.*?)\}', action_str)
        generate_mp3_match = re.match(r'GenerateMP3\{(.*?)\}', action_str)
        create_role_match = re.match(r'CreateRole\{(.*?)\}', action_str)
        send_image_match = re.match(r'SendImage\{(.*?)\}', action_str)
        if send_message_match:
            content = send_message_match.group(1)
            result = check_secondary(content)
            if result:
                action_list.append(SendMessageAction(result))
            else:
                action_list.append(SendMessageAction(content))
        elif generate_mp3_match:
            params = generate_mp3_match.group(1)
            txt, lg = params.split(";")
            result = check_secondary(txt)
            if result:
                action_list.append(GenerateMP3Action(result, lg))
            else:
                action_list.append(GenerateMP3Action(txt, lg))
        elif create_role_match:
            params = create_role_match.group(1)
            name, color = params.split(";")
            action_list.append(CreateRoleAction(name, color))
        elif send_image_match:
            url = send_image_match.group(1)
            action_list.append(SendImageFromURLAction(url))
    
    return action_list
