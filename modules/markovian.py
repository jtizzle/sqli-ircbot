#!/usr/bin/env python3

import random
from pprint import pprint
from random import choice

# End of Sentence for Markov chaining
EOS = ['.', '?', '!', 'k']


class Markovian:
    def markov(self):
        with open("txt_files/chatter.txt", "r") as smart_log:
            text = smart_log.read()
        print(text)
        words = text.split()
        print(words)
        d = self.build_dict(words)
        pprint(d)
        sent = self.generate_sentence(d)
        return sent

    def build_dict(self, words):
        d = {}
        for i, word in enumerate(words):
            try:
                first, second, third = words[i], words[i + 1], words[i + 2]
            except IndexError:
                break
            key = (first, second)
            if key not in d:
                d[key] = []
            d[key].append(third)
        return d

    def generate_sentence(self, d):
        li = [key for key in d.keys() if key[0][0].isupper()]
        key = choice(li)
        li = []
        first, second = key
        li.append(first)
        li.append(second)
        while True:
            try:
                third = choice(d[key])
            except KeyError:
                break
            li.append(third)
            if third[-1] in EOS:
                break
            else:
                key = (second, third)
                first, second = key
        return ' '.join(li)
