import os
from pyrogram import filters
from DazaiRobot import ptb as app 
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,InputMediaDocument
import asyncio
from lexica import AsyncClient
from math import ceil

MOD_LOAD = []
MOD_NOLOAD = []

class EqInlineKeyboardButton(InlineKeyboardButton):
    def __eq__(self, other):
        return self.text == other.text

    def __lt__(self, other):
        return self.text < other.text

    def __gt__(self, other):
        return self.text > other.text

def paginate_modules(page_n, module_dict, prefix, chat=None):
    modules = (
        sorted(
            [
                EqInlineKeyboardButton(
                    x.__mod__,
                    callback_data=f"{prefix}_module({chat},{x.__mod__.lower()})",
                )
                for x in module_dict.values()
            ]
        )
        if chat
        else sorted(
            [
                EqInlineKeyboardButton(
                    x.__mod__,
                    callback_data=f"{prefix}_module({x.__mod__.lower()})",
                )
                for x in module_dict.values()
            ]
        )
    )

    pairs = list(zip(modules[::3], modules[1::3], modules[2::3]))
    i = 0
    for m in pairs:
        for _ in m:
            i += 1
    if len(modules) - i == 1:
        pairs.append((modules[-1],))
    elif len(modules) - i == 2:
        pairs.append(
            (
                modules[-2],
                modules[-1],
            )
        )

    COLUMN_SIZE = 3

    max_num_pages = ceil(len(pairs) / COLUMN_SIZE)
    modulo_page = page_n % max_num_pages

    if len(pairs) > COLUMN_SIZE:
        pairs = pairs[modulo_page * COLUMN_SIZE : COLUMN_SIZE * (modulo_page + 1)] + [
            (
                EqInlineKeyboardButton(
                    "❮", callback_data=f"{prefix}_prev({modulo_page})"
                ),
                EqInlineKeyboardButton(
                    "❯ BACK ❮", callback_data=f"{prefix}_home({modulo_page})"
                ),
                EqInlineKeyboardButton(
                    "❯", callback_data=f"{prefix}_next({modulo_page})"
                ),
            )
        ]

    return pairs

def is_module_loaded(name):
    return (not MOD_LOAD or name in MOD_LOAD) and name not in MOD_NOLOAD

async def getFile(message):
    if not message.reply_to_message:
        return None
    if message.reply_to_message.document is False or message.reply_to_message.photo is False:
        return None
    if message.reply_to_message.document and message.reply_to_message.document.mime_type in ['image/png','image/jpg','image/jpeg'] or message.reply_to_message.photo:
        image = await message.reply_to_message.download()
        return image
    else:
        return None

async def getText(message):
    """Extract Text From Commands"""
    text_to_return = message.text
    if message.text is None:
        return None
    if " " in text_to_return:
        try:
            return message.text.split(None, 1)[1]
        except IndexError:
            return None
    else:
        return None

ImageModels = {
    "Meina Mix":2,
    "Cetus Mix":10,
    "DarkSushiMix":9,
    "DarkSushiMix V2":14,
    "Absolute Reality":13,
    "CreativeV2":12,
}

async def ImageGeneration(model,prompt):
    try:
        if model not in list(ImageModels.values()):
            return 1
        client = AsyncClient()
        output = await client.generate(model,prompt,"")
        if output['code'] != 1:
            return 2
        task_id, request_id = output['task_id'],output['request_id']
        await asyncio.sleep(20)
        tries = 0
        image_url = None
        resp = await client.getImages(task_id,request_id)
        while True:
            if resp['code'] == 2:
                image_url = resp['img_urls']
                break
            if tries > 15:
                break
            await asyncio.sleep(5)
            resp = await client.getImages(task_id,request_id)
            tries += 1
            continue
        return image_url
    except Exception as e:
        raise Exception(f"Failed to generate the image: {e}")




PromptDB = {}

@app.on_message(filters.command("draw"))
async def generate(_, message):
    global PromptDB
    prompt = await getText(message)
    if prompt is None:
        return await message.reply_text("No prompt given")
    user = message.from_user
    btns = []
    PromptDB[user.id] = {'prompt':prompt,'reply_to_id':message.id}
    for i in ImageModels:
        btns.append(InlineKeyboardButton(text=i,callback_data=f"draw.{ImageModels[i]}.{user.id}"))
    btns = [[btns[0],btns[1]],[btns[2],btns[3]],[btns[4],btns[5]]]
    await message.reply_photo("https://graph.org//file/a24ad0babb868d539b744.jpg", caption=f"**SELECT A MODEL TO GENERATE**",reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query(filters.regex("^draw.(.*)"))
async def draw(_,query):
    global PromptDB
    data = query.data.split('.')
    auth_user = int(data[-1])
    if query.from_user.id != auth_user:
        return await query.answer("Not Your Query!")
    promptdata = PromptDB.get(auth_user,None)
    if promptdata is None:
        return await query.edit_message_text("something went wrong report it at @DevsOops")
    await query.edit_message_text("Please wait, generating your image")
    img_url = await ImageGeneration(int(data[1]),promptdata['prompt'])
    if img_url is None or img_url == 2 or img_url ==1:
        return await query.edit_message_text("something went wrong report it at @DevsOops")
    images = []
    await query.message.delete()
    del PromptDB[auth_user]
    for i in img_url:
        images.append(InputMediaDocument(i, caption=f"YOUR PROMPT: {promptdata['prompt']}\n\n"))

    await app.send_media_group(
        chat_id=query.message.chat.id,
        media=images,
        reply_to_message_id=promptdata['reply_to_id']
    )




            
