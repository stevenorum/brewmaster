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

number_RE_list = [
'\d+',
'\d+/\d+',
'\d*\.\d+',
'\d+-\d+',
'\d+-\d+/\d+',
'\d+--\d+',
'\d+--\d+/\d+',
'\d+ \d+/\d+',
]

number_RE_prefix_list = [
'^',
'^~',
]

unit_RE_map = [
'ounce':['[oO]unce','[oO][zZ]',],
'pound':['[pP]ound','lb','lbs','#'],
'kilogram':['[kK]ilogram','[kK][gG]', '[kK]ilo'],
'gram':['[gG]ram','[gG]',''],
'AAU':['AAU','aau'],
'HBU':['alpha'],
'percent':['[pP]ercent','%'],
]

ingredient_RE='<span itemprop="ingredients">(?P<ingredient>.*)</span>'
rating_RE='<span itemprop="ratingValue">(?P<rating>\d\.\d)</span> stars based on <span itemprop="ratingCount">(?P<votes>\d+)</span> votes'
type_RE='<b>Beer Style:</b> (?P<type>.*)&nbsp;\(<a href="bjcpguidelines\.php\?id=\d+&amp;recipeid=(?P<id>\d+)" rel="nofollow">(?P<bjcp>[A-Z0-9]+)</a>\)<br>'
name_RE='<h1 itemprop="name">(?P<name>.*)</h1>'

# FUNCTIONS

def sort_by_rating(recipes):
    return sorted(recipes, key = lambda r:'{}.{}'.format(r['rating'],str(r['votes']).zfill(6)), reverse=True)

def get_number(ingredient):
    # consider changing to pull the first number in the string even if it isn't right at the beginning
    options = [None]
    for pref in number_RE_prefix_list:
        for RE in number_RE_list:
            n = re.search(pref+RE, ingredient)
            if n:
                options+=[n.group()]
    return sorted(options, key=lambda n: len(n) if n else -1, reverse=True)[0]

def get_units(ingredient):
    # have this go through the entire unit_RE_map and take whichever is matched with the earliest starting index, and then use its key in the dict instead of itself.
    return None

def get_ingredient(ingredient):
    # have this return everything after the end of the units.  I'll need to come up with a master list of all the ingredients to consider, and how to detect them.
    return None

def parse_ingredient(ingredient):
    # replace all of these with machine learning at some point, but it doesn't need to be now
    parts = {}
    parts['amount'] = get_number(ingredient)
    parts['units'] = get_units(ingredient)
    parts['ingredient'] = get_ingredient(ingredient)
    return parts

def main():
    parser = argparse.ArgumentParser(description='Clean recipes intoa  consistent format.')
    parser.add_argument("-p", "--path", metavar='P', help="Path of the directory in which to store the recipes.  Defaults to ./recipes/", default='recipes/')
    args = parser.parse_args()
    path = args.path

    recipes = []
    for f in os.listdir(path):
        full_path = os.path.join(path,f)
        with open(full_path, 'r') as recipe_file:
            recipe = json.load(recipe_file)
            recipes += [recipe]
    recipes = sort_by_rating(recipes)
#     for recipe in recipes:
#         print('{}: {} ({})'.format(recipe['name'], recipe['rating'], recipe['votes']))
    for recipe in recipes:
        for ingredient in recipe['ingredients']:
            print('{} : {}'.format(get_number(ingredient),ingredient))

if __name__ == "__main__":
    main()
