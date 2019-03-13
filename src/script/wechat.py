from wxpy import *
bot = Bot()

@bot.register(bot.file_helper, except_self=False)
def chat(msg):
    print(msg)

if __name__ == '__main__':
    myself = bot.self
    bot.file_helper.send('halo')
    embed()
