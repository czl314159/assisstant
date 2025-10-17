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
