from PIL import Image, ImageDraw, ImageFont
from random import randint

def make_text(text: str):
    arr = ['']
    words = text.split(' ')
    if not ' ' in text:
        words =  list(text)
    for word in words:
        if len(arr[-1] + word) > 27:
            arr.append(word)
        else:
            arr[-1] += ' ' + word
    if len(arr) > 5:
        return 'Слишком много символов :('
    return '\n'.join(arr)


# p-from - 8
# p-for - 12
#
#

def create_picture(color, text, p_from, p_for):
    img = Image.open(f'patterns/{color}.png')
    text = make_text(text)
    edit = ImageDraw.Draw(img)

    big_font = ImageFont.truetype('patterns/baloo-cyrillic.ttf', 125)
    small_font = ImageFont.truetype('patterns/baloo-cyrillic.ttf', 100)

    edit.text((230, 550), text, font=big_font, fill='#313131')
    edit.text((630, 1360), p_from, font=small_font, fill='#313131')
    edit.text((485, 1473), p_for, font=small_font, fill='#313131')

    number = randint(0, 1000000)
    img.save(f"pictures/{number}.png")
    return number

