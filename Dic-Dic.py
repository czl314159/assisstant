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

for user,inf in users.items():
    print(user)
    full_name = inf['first']+inf['last']
    location = inf['location']
    print("\tFull name: " + full_name.title()) 
    print("\tLocation: " + location.title())
