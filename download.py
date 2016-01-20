#!/usr/bin/env python

import argparse
import json
import os.path
import re
import urllib2

'''
Currently this takes ~1.5 seconds per recipe.  Not sure if there's a good way to improve that.
'''

# MAGIC CONSTANTS

ingredient_RE='<span itemprop="ingredients">(?P<ingredient>.*)</span>'
rating_RE='<span itemprop="ratingValue">(?P<rating>\d\.\d)</span> stars based on <span itemprop="ratingCount">(?P<votes>\d+)</span> votes'
type_RE='<b>Beer Style:</b> (?P<type>.*)&nbsp;\(<a href="bjcpguidelines\.php\?id=\d+&amp;recipeid=(?P<id>\d+)" rel="nofollow">(?P<bjcp>[A-Z0-9]+)</a>\)<br>'
name_RE='<h1 itemprop="name">(?P<name>.*)</h1>'

# FUNCTIONS

def load_recipe(id):
    recipe = urllib2.urlopen('http://beerrecipes.org/showrecipe.php?recipeid={}'.format(id)).read()
    if '<title>Find a Beer Recipe' in recipe:
        raise RuntimeError('Recipe not found')
    return recipe.split('\n')

def parse_recipe(recipe):
    beer = {'ingredients':[], 'rating':2, 'votes':0, 'source':'beerrecipes.com'}
    for line in recipe:
        if 'itemprop="ingredients"' in line:
            beer['ingredients'] += [re.search(ingredient_RE, line).group('ingredient').strip()]
        if 'ratingValue' in line:
            m = re.search(rating_RE, line)
            if m:
                beer['rating'] = m.group('rating').strip()
                beer['votes'] = m.group('votes').strip()
            else:
                beer['rating'] = 0
                beer['votes'] = 0
        if '<b>Beer Style:</b>' in line:
            m = re.search(type_RE, line)
            beer['style'] = m.group('type').strip()
            beer['bjcp'] = m.group('bjcp').strip()
            beer['id'] = m.group('id').strip()
        if '<h1 itemprop="name">' in line:
            beer['name'] = re.search(name_RE,line).group('name').strip()
    return beer

def save_recipe(recipe, path='recipes/'):
    filename = 'recipe-{}-{}.json'.format(recipe['id'].zfill(5), recipe['name'].translate(None,' /.,<>{}[]|+=-^%$~`;:\'"-?#&!()\\'))
    with open(os.path.join(path, filename), 'w') as f:
        json.dump(recipe, f, sort_keys=True, indent=4, separators=(',', ': '))

def main():
    parser = argparse.ArgumentParser(description='Download recipes.')
    parser.add_argument('-s', '--start', metavar='S', type=int, help='Index of first recipe to download.', default=1)
    parser.add_argument('-f', '--finish', metavar='F', type=int, help='Index of last recipe to download.', default=100)
    parser.add_argument("-p", "--path", metavar='P', help="Path of the directory in which to store the recipes.  Defaults to ./recipes/", default='recipes/')
    args = parser.parse_args()

    for i in xrange(args.start,args.finish+1):
        try:
            recipe = parse_recipe(load_recipe(i))
            save_recipe(recipe)
            print('{} (#{}) saved'.format(recipe['name'],recipe['id']))
        except RuntimeError as e:
            print('No recipe found with ID {}'.format(i))

if __name__ == "__main__":
    main()
