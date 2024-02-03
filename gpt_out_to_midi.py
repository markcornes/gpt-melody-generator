import numpy as np
import tools
import stock_velocities

if __name__ == '__main__':
    gpt_file_number = '13'
    # text_fname = 'text from gpt\\' + gpt_file_number
    text_fname = '1706690882\\1706690882'

    with open(text_fname+'.txt', 'r') as f:
        raw_text = f.read()
    notes = tools.text_to_notes(raw_text)
    stock_name = 'MSFT'
    velocities = stock_velocities.stock_velocities(f'stock data\\{stock_name}.csv', len(notes))


    for i in range(len(notes)):
        print(velocities[i])
        notes[i].velocity = int(velocities[i])

    tools.midi_maker(notes, 'generated midi\\'+gpt_file_number+'_'+stock_name)
    tools.compare_to_pieces(notes)