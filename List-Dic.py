"""
alien_0 = {'color': 'green', 'points': 5} 
alien_1 = {'color': 'yellow', 'points': 10} 
alien_2 = {'color': 'red', 'points': 15}
print(alien_0)

aliens = [alien_0, alien_1, alien_2] 
for alien in aliens: 
    print(alien)
"""

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