import tools, tiktoken, os, time, pickle
from openai import OpenAI
from tools import Note

# MODEL = 'gpt-3.5-turbo-0125'
MODEL = 'gpt-4-0125-preview'
def num_tokens_from_messages(messages, model='gpt-4-0125-preview'):
  """
  Returns the number of tokens used by a list of messages.
  Stolen from OpenAI API documentation.
  """
  try:
      encoding = tiktoken.encoding_for_model(model)
  except KeyError:
      encoding = tiktoken.get_encoding("cl100k_base")
  num_tokens = 0
  for message in messages:
      num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
      for key, value in message.items():
          num_tokens += len(encoding.encode(value))
          if key == "name":  # if there's a name, the role is omitted
              num_tokens += -1  # role is always required and always 1 token
  num_tokens += 2  # every reply is primed with <im_start>assistant
  return num_tokens

def generate_melody(api_key, instruct, examples, prompt_modifier=''):
    """
    Takes strings - API key, instructions, and examples.
    Checks if user wants to proceed, given size of input when tokenised.
    Returns gpt-generated melody string.
    """

    instruct_lines = instruct.splitlines()
    message_list = []
    for i in range(len(instruct_lines)-1):
        role, content = instruct_lines[i].split(';')
        message_list.append({'role':role, 'content':content})

    print(message_list)
    last_role, last_content = instruct_lines[-1].split(';')
    message_list += [{'role':'user', 'content':examples},{'role':last_role, 'content':last_content+prompt_modifier}]


    # message_list = [{'role':'system', 'content':'You are a helpful data generator: a creative music writer that only outputs melodies in the requested format.'},
    #               {'role':'user', 'content':'You will compose an original melody in a similar to example pieces I will provide. Ensure that the melody is not plagiarised from the examples.'},
    #               {'role':'user', 'content':'The melodies will be a number of pieces formatted as comma-separated values with the following heading: time,duration,pitch,velocity , where time is the position in the track, in 16th notes (semiquavers) since the beginning of the piece; duration is length of note in 16th notes; and pitch and velocity are in the midi format.'},
    #               {'role':'user', 'content':examples},
    #               {'role':'user', 'content':'Generate a melody similar in style to these. Respond with only the melody, and in exactly the format described. Never leave a melodic idea unfinished. Do not include any accompanying text. '+prompt_modifier}]

    consent = input(f'{num_tokens_from_messages(message_list)} prompt tokens counted.\n'
                     f'Would you like to proceed? ("yes" to proceed) >>> ')

    if consent.lower() != "yes":
        print('Aborting')
        return

    print('Querying GPT API...')
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        # model='gpt-3.5-turbo-0125',
        model='gpt-4-0125-preview',
        messages=message_list
    )
    return response

with open('api_key.txt', 'r') as f:
    API_KEY = f.read()

if __name__ == '__main__':
    # RANGE = range(2,6)
    RANGE = [2,4,5,13,15]

    timestamp = f'{time.time():.0f}'
    new_fname = f'generated data\\{timestamp}'
    examples_fname = new_fname+'\\data.txt'

    with open('pieces.pickle', 'rb') as f:
        pieces = pickle.load(f)

    # CHOOSE DATA RANGE HERE

    if not os.path.exists(new_fname):
        os.makedirs(new_fname)

    tools.generate_text_data(pieces, f'{new_fname}\\data.txt', RANGE)

    with open(examples_fname, 'r') as f:
        examples = f.read()

    with open('instruct.txt', 'r') as f:
        instruct = f.read()

    response = generate_melody(API_KEY, instruct, examples, prompt_modifier='Liberally add ornamental 8th notes (duration 2) and interesting rhythms. Add occasional 16th notes (duration 1).')

    if response is not None:
        melody_text = response.choices[0].message.content
        with open(f'{new_fname}\\{timestamp}.txt', 'w') as f:
            f.write(melody_text)

        generated_piece = tools.text_to_notes(melody_text)
        tools.midi_maker(generated_piece,f'{new_fname}\\{timestamp}')

        tokens = response.usage.total_tokens
        print(f'total tokens used: {tokens}')
        log_string = tools.compare_to_pieces(generated_piece)
        with open(f'{new_fname}\\{timestamp}_log.txt', 'w') as f:
            f.write(log_string)