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

unit_RE_map = {
    'ounce':['[oO]unce','[oO][zZ]',],
    'pound':['[pP]ound','lb','lbs','#'],
    'kilogram':['[kK]ilogram','[kK][gG]', '[kK]ilo'],
    'gram':['[gG]ram',' [gG] ','\d[gG] '],
    'AAU':['AAU','aau','[aA]lpha'],
    'HBU':['HBU'],
    'percent':['[pP]ercent','%'],
    'gallon':['[gG]al','[gG]allon'],
    'liter':['[lL]iter','[lL]itre',' [lL] ','\d[lL] '],
    'milliliter':['[mM][lL]','[mM]illi[lL]iter','[mM]illi[lL]itre'],
    'milligram':['[mM][gG]','[mM]illi[gG]ram'],
    'teaspoon': ['[tT][sS][pP]','[tT]easpoon'],
    'tablespoon': ['[tT][bB][sS]','[tT]ablespoon'],
    'cup': ['[cC]up'],
    'package': ['[pP][kK][gG]','[pP]ackage','[pP]ack'],
    'pint': ['[pP][tT]','[pP]int'],
    'can': ['[cC]an'],
    'pinch': ['[pP]inch'],
    'stick': ['[sS]tick'],
}

master_units = {
    'volume':'milliliters',
    'weight':'grams',
}

conversion_factors = {
    'ounce':{
        'type':'weight',
        'factor':28.3495,
        },
    'pound':{
        'type':'weight',
        'factor':453.592,
        },
    'kilogram':{
        'type':'weight',
        'factor':1000,
        },
    'gram':{
        'type':'weight',
        'factor':1,
        },
    'gallon':{
        'type':'volume',
        'factor':3785.41,
        },
    'liter':{
        'type':'volume',
        'factor':1000,
        },
    'milliliter':{
        'type':'volume',
        'factor':1,
        },
    'milligram':{
        'type':'weight',
        'factor':.001,
        },
    'teaspoon':{
        'type':'volume',
        'factor':4.92892,
        },
    'tablespoon':{
        'type':'volume',
        'factor':14.7868,
        },
    'cup':{
        'type':'volume',
        'factor':236.588,
        },
    'pint':{
        'type':'volume',
        'factor':473.176,
        },
    }

# this needs to get a lot more detail at some point, but let's get a simple first version working now.
type_RE_map = {
    'yeast':[
        '[yY]east',
        ],
    'hops': [
        ' [hH]op[s$ ]{1}',
        # '[hH]ood',
        # '[nN](orthern){0,1}(\.){0,1} [bBrewer]',
        # '[hH]allertau',
        # '[sS]aaz',
        # '[gG]olding',
        # '[tT]e(t){1,3}nang',
        '[pP]ellet',
        '[lL]eaf',
        # '[cC]hinook',
        # '[cC]ascade',
        '[pP]lugs',
        # '[fF]uggle',
        # '[bB]ullion',
        # '[pP]erle',
        # '[cC]entennial',

#        '[aA]lpha',
        '[aA][aA][uU]',
#        '%',
        ],
    'grain':[
        '[cC]rystal',
        '[cC]ara',
        '[bB]arley',
        '[bB]arely',
        '[mM]alt',
        '[mM]aize',
        '[pP]atent',
        '[mM]unich',
        '[oO]ats',
        '[wW]heat',
        '[bB]iscuit',
        '[gG]rain',
        '[rR]ow',
        '[kK]lages',
        '[sS]pecial [bB]',
        ],
    'extract':[
        '[dD][mM][eE]',
        '[eE]xtract',
        '[mM][eE]',
        '[mM]unton',
        ],
    'other':[
        '[mM]oss',
        '[sS]yrup',
        '[gG]ypsum',
        '[pP]eel',
        '[sS]alt',
        '[hH]oney',
        '[sS]ugar',
        '[rR]ice',
        '[dD]extr',
        '[lL]icorice',
        '[aA]cid',
        '[gG]elatin',
        '[fF]ining',
        '[oO]ak',
        '[cC]innamon',
        '[pP]oly[cC]lar',
        '[gG]inger',
        '[cC]offee',
        '[cC]hoco',
        '[aA]llspice',
        '[cC]loves',
        '[lL]actose',
        '[mM]olasses',
        '[eE]spresso',
        '[cC]ocoa',
        ],
    }

subtype_RE_map = {
    'hops':{
        'fuggle':['[fF]uggle'],
        'cascade':['[cC]ascade'],
        'mt. hood':['[hH]ood'],
        'saaz':['[sS]aaz','[sS]azz'],
        'nugget':['[nN]ugget'],
        'hallertau':['[hH]a(l){1,3}ert'],
        'mittelfruh':['[mM]ittelfruh'],
        'tettnanger':['[tT]e(t){1,3}(n){0,2}[ae]ng'],
        'challenger':['[cC]hallenger'],
        'perle':['[pP]erl'],
        'northern brewer':['[nN](orthern){0,1}(\.){0,1} [bB]rewer','[bB]rewer','[nN][bB]'],
        'willamette':['[wW]i(l){1,3}am'],
        'noble':['[nN]oble'],
        'chinook':['[cC]hi(n){1,3}(o){1,3}k'],
        'cluster':['[cC]luster'],
        'hersbrucker':['[hH]e(r){1,3}sbruck'],
        'talisman':['[tT]alisman'],
        'kent goldings':['[kK]ent [gG]olding','[gG]olding'],
        'styrian goldings':['[sS]tyrian [gG]olding','[sS]tyrian'],
        'bullion':['[bB]u(i){0,1}llion'],
        'eroica':['[eE]roic'],
        'bramling':['[bB]ram(b){0,1}l'],
#        'crystal':['[cC]rystal'],
        'galena':['[gG]alena'],
        'centennial':['[cC]entennial'],
        'columbus':['[cC]olumbus'],
        'ekg':['[eE][kK][gG]'],
        'olympic':['[oO]lympic'],
        'target':['[tT]arget'],
        }
}

hops_alpha_map = {
        'fuggle':4.5,
        'cascade':7,
        'mt. hood':4.8,
        'saaz':3.5,
        'nugget':14,
        'hallertau':4,
        'mittelfruh':3.75,
        'tettnanger':4.5,
        'challenger':8.5,
        'perle':8.2,
        'northern brewer':7.8,
        'willamette':4.5,
        'noble':4.25,
        'chinook':13,
        'cluster':6.5,
        'hersbrucker':4,
        'talisman':8,
        'kent goldings':5,
        'styrian goldings':5.5,
        'bullion':7.5,
        'eroica':12,
        'bramling':6.5,
#        'crystal':4.3,
        'galena':13,
        'centennial':7.8,
        'columbus':15,
        'ekg':5,
        'olympic':12,
        'target':11.5,
        }

for type in subtype_RE_map.keys():
    for subtype in subtype_RE_map[type].keys():
        type_RE_map[type] += subtype_RE_map[type][subtype]

ingredient_RE='<span itemprop="ingredients">(?P<ingredient>.*)</span>'
rating_RE='<span itemprop="ratingValue">(?P<rating>\d\.\d)</span> stars based on <span itemprop="ratingCount">(?P<votes>\d+)</span> votes'
type_RE='<b>Beer Style:</b> (?P<type>.*)&nbsp;\(<a href="bjcpguidelines\.php\?id=\d+&amp;recipeid=(?P<id>\d+)" rel="nofollow">(?P<bjcp>[A-Z0-9]+)</a>\)<br>'
name_RE='<h1 itemprop="name">(?P<name>.*)</h1>'

percent_RE='((?P<percent1>\d{1,3}(\.\d){0,1})( ){0,1}(%|[pP]ercent|[aA]l)|lpha (?P<percent2>\d{1,3}(\.\d){0,1}))'
aau_RE='(?P<aau>\d{1,3}(\.\d){0,1})( ){0,1}([aA][aA][uU])'
minute_RE='(?P<minutes>\d{1,3}(\.\d){0,1})( ){0,1}[mM][iI][nN]'
hour_RE='(?P<hours>\d{1,3}(\.\d){0,1})( ){0,1}[hH][oOrR]'
last_RE='[ +](?P<last>\d{1,3}(\.\d){0,1})$'
# FUNCTIONS

def sort_by_rating(recipes):
    return sorted(recipes, key = lambda r:'{}.{}'.format(r['rating'],str(r['votes']).zfill(6)), reverse=True)

def convert_to_float(number):
    if not number:
        return None
    cleaned = number.replace('-',' ').replace('  ',' ')
    parts = cleaned.split(' ')
    sum = 0
    for part in parts:
        try:
            sum += float(part)
        except ValueError:
            try:
                fraction = part.split('/')
                if len(fraction) == 2:
                    sum += float(fraction[0])/float(fraction[1])
            except ValueError:
                pass
    return sum


def standardize_units(number, unit):
    if number and unit in conversion_factors.keys():
        type = conversion_factors[unit]['type']
        factor = conversion_factors[unit]['factor']
        new_unit = master_units[type]
        new_number = convert_to_float(number) * factor
        return new_number, new_unit
    return number, unit

def get_number(ingredient):
    # consider changing to pull the first number in the string even if it isn't right at the beginning
    options = [None]
    for pref in number_RE_prefix_list:
        for RE in number_RE_list:
            n = re.search(pref+RE, ingredient)
            if n:
                options+=[n.group()]
    return sorted(options, key=lambda n: len(n) if n else -1, reverse=True)[0]

def get_units(ingredient, verbose=False):
    return match_regex_map(ingredient, unit_RE_map, verbose)

def get_type(ingredient, verbose=False):
    # have this return everything after the end of the units.  I'll need to come up with a master list of all the ingredients to consider, and how to detect them.
    return match_regex_map(ingredient, type_RE_map, verbose)

def get_subtype(ingredient, type):
    RE_map = subtype_RE_map.get(type, None)
    if RE_map:
        return match_regex_map(ingredient.lower(), subtype_RE_map[type])
    else:
        return None

def get_minutes(ingredient):
    h = re.search(hour_RE, ingredient)
    m = re.search(minute_RE, ingredient)
    l = re.search(last_RE, ingredient)
    hours = 0.0
    minutes = 0.0
    if h:
        hours = float(h.group('hours'))
    if l:
        minutes = float(l.group('last'))
    if m: # yes, this might overwrite the other guess, but if we find this one it takes precedence
        minutes = float(m.group('minutes'))
    return minutes + 60*hours

def get_alpha(ingredient):
    subtype = get_subtype(ingredient,'hops')
    p = re.search(percent_RE, ingredient)
    a = re.search(aau_RE, ingredient)
    if p:
        percent = p.group('percent1') if p.group('percent1') else p.group('percent2')
    elif subtype:
        percent = hops_alpha_map[subtype]
    else:
        percent = None
    aau = a.group('aau') if a else None
    if aau and not percent:
        return float(aau)
    elif percent and not aau:
        amount, unit = standardize_units(get_number(ingredient), get_units(ingredient))
        if amount and unit==master_units['weight']:
            return float(percent) * (amount / conversion_factors['ounce']['factor'])
        else:
            return float(percent)
    elif percent and aau:
        amount, unit = standardize_units(get_number(ingredient), get_units(ingredient))
        if amount and unit==master_units['weight']:
            return float(percent) * (amount / conversion_factors['ounce']['factor'])
        else:
            return float(aau)
    else:
        return None

def match_regex_map(ingredient, RE_map, verbose=False):
    unit_indices = {}
    unit_lengths = {}
    for unit in RE_map.keys():
        unit_indices[unit] = len(ingredient) + 5
        unit_lengths[unit] = 0
        for RE in RE_map[unit]:
            u = re.search(RE, ingredient)
            if u:
                if verbose:
                    print("RE matches: " + RE)
                new_index = u.start(0)
                if new_index < unit_indices[unit]:
                    unit_indices[unit] = new_index
                if new_index <= unit_indices[unit]:
                    new_len = len(u.group())
                    if new_len > unit_lengths[unit]:
                        unit_lengths[unit] = new_len
    chosen_unit = None
    index = len(ingredient) + 3
    length = 0
    for unit in unit_indices.keys():
        i = unit_indices[unit]
        l = unit_lengths[unit]
        if i < index:
            index = i
            chosen_unit = unit
            length = l
        elif i == index and l > length:
            index = i
            chosen_unit = unit
            length = l
    return chosen_unit

def parse_ingredient(ingredient):
    # replace all of these with machine learning at some point, but it doesn't need to be now
    parts = {}
    parts['amount'] = get_number(ingredient)
    parts['units'] = get_units(ingredient)
    parts['ingredient'] = get_ingredient(ingredient)
    return parts

def parse_recipes(path, start, finish):
    recipes = []
    for f in os.listdir(path):
        index = int(f.split('-')[1])
        if index <= finish and index >= start:
            full_path = os.path.join(path,f)
            with open(full_path, 'r') as recipe_file:
                recipe = json.load(recipe_file)
                recipes += [recipe]
    recipes = sort_by_rating(recipes)
    #     for recipe in recipes:
    #         print('{}: {} ({})'.format(recipe['name'], recipe['rating'], recipe['votes']))
    success = 0
    failure = 0
    for recipe in recipes:
        full_parse = True
        for ingredient in recipe['ingredients']:
            number = get_number(ingredient)
            units = get_units(ingredient)
            snumber, sunits = standardize_units(number, units)
            type = get_type(ingredient)
            subtype = get_subtype(ingredient, type)
            if type == 'hops' and (not subtype or not get_alpha(ingredient)):
                full_parse = False
            if not type:
                full_parse = False
            if type == 'hops':
                print('{}  -  {}  -  {}'.format(get_alpha(ingredient),get_minutes(ingredient), ingredient))
                # print(ingredient)
    #             print('{} -> {}'.format(number, convert_to_float(number)))
    #             print('{}, {}, {}'.format(snumber, sunits, type))
        if full_parse:
            print(recipe['name'])
            success+=1
        else:
            failure+=1
    print("Fully-parsed recipes: {}".format(success))
    print("Non-parsed recipes: {}".format(failure))

def main():
    parser = argparse.ArgumentParser(description='Clean recipes into a consistent format.')
    parser.add_argument('-s', '--start', metavar='S', type=int, help='Index of first recipe to read.', default=1)
    parser.add_argument('-f', '--finish', metavar='F', type=int, help='Index of last recipe to read.', default=100)
    parser.add_argument("-p", "--path", metavar='P', help="Path of the directory in which to store the recipes.  Defaults to ./recipes/", default='recipes/')
    args = parser.parse_args()
    path = args.path

#    get_type('3.3 pounds, John Bull dark extract', verbose=True)

    parse_recipes(args.path, args.start, args.finish)


if __name__ == "__main__":
    main()
