import tools, pickle
from tools import Note

with open('pieces.pickle', 'rb') as f:
    pieces = pickle.load(f)

number = 30

print(pieces[number][0].key)
tools.midi_maker(pieces[number], f"{number} special")
