# PROBLEM WITH TIMING IS THAT THE TIME DELAY IS ADDED BEFORE A NOTE ON AND BEFORE NOTE OFF:
# ACCOUNT FOR THIS FOR NEXT NOTE BY FINDING DIFFERENCE AND PUTTING IT BEFORE NOTE OFF OF PREVIOUS NOTE

import re, time, pickle
from statistics import median

VEL = 63
DELTA_DIV = 240  # number of ticks per quarter note

class Note:
    """
        st:       16th notes since start of piece
        pitch:    semitones above C4
        duration: in 16th notes
        key:      number of sharps (+) or flats (-)
        time:     16th notes per bar
    """

    def __init__(self, st, pitch, duration, key, time, velocity=VEL):
        self.st = int(st)
        self.pitch = int(pitch)
        self.duration = float(duration)
        self.key = int(key)
        self.time = int(time)
        self.velocity = int(velocity)

    def __str__(self):
        return 'time: ' + str(self.st) + ', pitch: ' + str(self.pitch) + ', length: ' + str(self.duration)

    def demodulate(self):
        """standardises notes to be CMaj/Am"""
        if self.key < 0:
            self.pitch += -self.key*7 % 12
        if self.key > 0:
            self.pitch += self.key*5 % 12

# FUNCTIONS
def generate_text_data(piece_list, fname, indices):
    C_maj_mod = [0,2,4,5,7,9,11]

    out_string = ''

    for i in indices:
        piece = piece_list[i]
        out_string += f'Piece {i}\ntime,duration,pitch,velocity\n'
        for note in piece:
            note.demodulate()
            out_string += f'{note.st},{note.duration:.0f},{note.pitch},127\n'

        out_string += '\n'

    # measuring the percentage of notes in the C Major scale in each piece, after normalising,
    #       checking it is close to 100% for each piece
    #       (pieces in minor keys often contain more non-diatonic notes from harmonic/melodic minor scales).
    if __name__ == '__main__':
        for n in range(len(pieces)):
            diatonic = 0
            for note in pieces[n]:
                if note.pitch % 12 in C_maj_mod:
                    diatonic += 1
            print(f'Piece {n}: {100*diatonic/len(pieces[n]):.0f}%')

    with open(fname, 'w') as f:
        f.write(out_string)

def v_length(num):
    out = []
    if num > 127:
        out.append(int(num//127 + 128))
    out.append(int(num%127))
    return out

def note_to_midi(note, current_time):
    """max note duration of 90 seconds"""
    out_list = [0]
    # out_list = v_length((note.st - current_time))

    out_list += [144, note.pitch, note.velocity]
    d_time = (note.duration/4)*DELTA_DIV

    out_list += v_length(d_time)
    time_change = note.duration # THIS WILL NOT SUPPORT TIMES DISSIMILAR TO EXPECTED, I.E. OVERLAPPING NOTES

    out_list += [128, note.pitch, 0]


    return out_list, time_change

def normaliser(bytes, length):
    """turns list of bytes into set bit length"""

    return [0 for i in range(0,length-len(bytes))] + bytes

def file_strip():
    raw_pieces = ['']

    with open('chorales-lisp.txt', 'r') as f:
        data = f.read()

    i = 0

    for datum in data:
        if datum == '\n':
            i += 1
            raw_pieces.append('')
            continue
        raw_pieces[i] += datum

    separated_pieces = [a for a in raw_pieces if a]

    digits = str([0,1,2,3,4,5,6,7,8,9])


    for n in range(0,len(separated_pieces)):
        piece = separated_pieces[n]
        m = 0


        while m < len(piece):

            if piece[m] == ' ' and piece[m+1] in digits and piece[m+2] not in digits:
                piece = piece[:m+1] + '0' + piece[m+1:]

            m += 1
        separated_pieces[n] = piece


    better_pieces = []
    for piece in separated_pieces:
        trash, piece = piece.split(' ', 1)
        piece = piece[1:len(piece)-2]
        better_pieces.append(piece)

    split_pieces = []
    for n in range(0,len(better_pieces)):
        split_pieces.append(better_pieces[n].split(")("))

    pieces_notes = []

    for n in range(0,len(split_pieces)):
        pieces_notes.append([])
        for note in split_pieces[n]:
            stripped_note = re.sub('( |[(]|[)])', '', note)
            good_note = re.sub('(st|pitch|dur|keysig|timesig|fermata)', ' ' , stripped_note).split(' ')

            new_note = Note(good_note[1], good_note[2], good_note[3], good_note[4], good_note[5])
            pieces_notes[n].append(new_note)


    with open('pieces.pickle', 'wb') as f:
        pickle.dump(pieces_notes, f)

    return pieces_notes

def find_minmax(pn):
    biggest = 0
    longest = 400

    for piece in pn:
        lengths = []
        length = 0
        for note in piece:
            length += note.duration
        # print(length)
        longest = min(length, longest)
        lengths.append(length)
        biggest = max(biggest, len(piece))

    print(biggest)

def midi_maker(piece, filename):
    file_header = [77, 84, 104, 100, 0, 0, 0, 6, 0, 1, 0, 2, 0, DELTA_DIV, 77, 84, 114, 107, 0, 0, 0]
    time_sig = [0, 255, 88, 4, 4, 2, 18, 8]
    time_sig = []
    tempo = [0, 255, 81, 3, 7, 0, 0]
    track_end = [0, 255, 47, 0]

    file_header.append(len(time_sig)+len(tempo) + len(track_end))

    contents = []
    current_time = 0

    for note in piece:
        note.demodulate()
        midi, time_change = note_to_midi(note, current_time)
        current_time += time_change
        contents += midi

    new_track = [77, 84, 114, 107] + normaliser(v_length(len(contents)+len(track_end)),4) # +LENGTH!!

    write_to = bytes(file_header + time_sig + tempo + track_end + new_track + contents + track_end)

    with open(f'{filename}.mid', 'wb') as f:
        f.write(write_to)

def comparison(piece1, piece2):
    """
        Compares two melodies to measure similarity.
        Returns a score for how similar they are (0-1).
    """

    # add padding
    for note in piece1:
        note.demodulate()
    for note in piece2:
        note.demodulate()
    while len(piece1) < len(piece2): piece1.append(Note(0, 0, 0, 0, 0))
    while len(piece1) > len(piece2): piece2.append(Note(0,0,0,0,0))

    # compare chains
    longest_chain = 0

    for note1 in piece1:
        chain = 0
        for i in range(0,len(piece2)):
            if piece1[i].pitch == piece2[i].pitch and piece1[i].duration == piece2[i].duration:
                chain += 1
            else:
                longest_chain = max(longest_chain, chain)
                chain = 0

    # compare whole piece, note for note, at different shifts
    most_copied = 0

    for shift in range(len(piece1)):
        number_copied = 0
        for i in range(len(piece1)):
            j = (i+shift)%len(piece1)
            if piece1[i].pitch == piece2[j].pitch: number_copied += 1
        most_copied = max(most_copied,number_copied)

    return longest_chain/len(piece1), most_copied/len(piece1)

def text_to_notes(raw_text):
    text = raw_text.splitlines()
    # print(text[0])

    notes = []
    for line in text:
        entries = line.split(',')
        # print(entries)
        try:
            notes.append(Note(entries[0], entries[2], entries[1], 0, 0, velocity=entries[3]))
        except:
            continue

    return notes

def compare_to_pieces(notes):
    with open('pieces.pickle', 'rb') as f:
        pieces = pickle.load(f)

    out_string = ""

    biggest_chain = 0
    most_similar = 0
    sum_of_similar = 0
    max_sim_number = 0
    max_chain_number = 0
    for i in range(0,len(pieces)):
        chain, similar = comparison(pieces[i], notes)
        sum_of_similar += similar
        p_string = f"Piece {i}: {chain*100:.1f}% longest chain, {similar*100:.1f}% similar"
        out_string += p_string + "\n"
        print(p_string)
        if chain > biggest_chain:
            biggest_chain = chain
            max_chain_number = i
        if similar > most_similar:
            most_similar = similar
            max_sim_number = i

    final_string = f"\nLongest chain: {biggest_chain*100:.1f}% (Piece {max_chain_number})\nMost similar: {most_similar*100:.1f}% (Piece {max_sim_number})\nMean similarity: {sum_of_similar:.1f}%"
    out_string += final_string
    print(final_string)

    return out_string

if __name__ == "__main__":
    PIECE_N = 81 # number of piece (from 0 - 99) that we will convert to midi
    PIECE = file_strip()[PIECE_N]
    midi_maker(PIECE, f'{time.time():.0f}')