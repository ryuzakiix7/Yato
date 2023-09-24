import requests as r
from pyrogram.types import InputMediaPhoto
from pyrogram import filters, Client
from pyrogram.types import Message

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

@Client.on_message(filters.command("images"))
async def get_images(_, message: Message):
    query = await getText(message)
    text = query.replace(" ", "%")
    response = r.get(f"https://nova-api-seven.vercel.app/api/images?name={text}")
    image_data = response.json()
    image_urls = image_data.get("image_urls", [])[:10]
    ab = await message.reply("Getting Your Images... Wait A Min..")
    
    if not image_urls:
        await ab.edit("No Results Found. Please Try Something Else!")
    else:
        Ok = []
        for a in image_urls:
            Ok.append(InputMediaPhoto(a))
        try:
            await message.reply_media_group(media=Ok)
            await ab.delete()
        except Exception:
            await ab.edit("Error occurred while sending images. Please try again.")
