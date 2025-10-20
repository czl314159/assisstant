# 字典存储字典示例
print("Dictionaries storing dictionaries:")
users = {
    'aeinstein': { 
        'first': 'albert', 
        'last': 'einstein', 
        'location': 'princeton', 
        }, 
    'mcurie': { 
        'first': 'marie', 
        'last': 'curie', 
        'location': 'paris', 
        }, 
    }

for user,inf in users.items(): # 遍历字典
    print(user) # 打印键
    full_name = inf['first']+inf['last'] # 拼接值
    location = inf['location'] # 赋值值
    print("\tFull name: " + full_name.title()) # 打印赋值值
    print("\tLocation: " + location.title()) # 打印赋值值
print("..."*30)

# 列表存储字典示例
print("Lists storing dictionaries:")
aliens=[]

for i in range(31):
    new= {'color': 'green', 'points': 5, 'speed': 'slow'}
    aliens.append(new)

for alien in aliens[:5]: 
    print(alien) 
print("...")

print("Total number of aliens: " + str(len(aliens)))
print("..."*30)

# 列表存储字典示例
print("Lists storing dictionaries example 2:")
alien_0 = {'color': 'green', 'points': 5} 
alien_1 = {'color': 'yellow', 'points': 10} 
alien_2 = {'color': 'red', 'points': 15}
print(alien_0)

aliens = [alien_0, alien_1, alien_2] 
for alien in aliens: 
    print(alien)
print("..."*30)

# 字典存储列表示例
print("Dictionaries storing lists:")
favorite_languages = { 
 'jen': ['python', 'ruby'], 
 'sarah': ['c'], 
 'edward': ['ruby', 'go'], 
 'phil': ['python', 'haskell'], 
 }

for name,lan in favorite_languages.items():
    print("\n" + name.title() + "'s favorite languages are:")
    for language in lan: 
        print("\t" + language.title())
print("..."*30)

# Helloworld示例
print("Hello World Example:")
mes="Hello world too"
print("Hello World")

name='ha ha'
print(name.title())
print(name+" "+mes)
print("Lang:\n\tPython\n\tC\n\tJava")

getin=input("Please Input:")
print(getin)