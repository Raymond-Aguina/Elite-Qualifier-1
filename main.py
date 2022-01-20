import time
import sys
import threading
from operator import itemgetter


dict_letters = {}
letters_list = []
alphabet = "abcdefghijklmnopqrstuvwxyz"
punctuation_marks = "!()-[]{};:'\"\,<>./?@#$%^&*_~"
question_words = {"who", "what", "when", "where", "why", "how", "whose", "does", "which", }

# load dictionary words from file
def load_words():
  all_words = []
  start_time = time.time()
  
  with open('words_alpha.txt', 'r') as f:
    for line in f:
      all_words.append(line.rstrip())
  end_time = time.time()

  elapsed_time = end_time - start_time
  # log words loaded and elapsed time
  print('Loaded ' + str(len(all_words)) + ' words in ' + f'{elapsed_time:.2f}' + ' seconds.')

  return all_words


def load_common_words():
  common_words = []
  start_time = time.time()
  
  with open('common_words.txt', 'r') as f:
    for line in f:
      common_words.append(line.rstrip())
  end_time = time.time()

  elapsed_time = end_time - start_time
  # log words loaded and elapsed time
  print('Loaded ' + str(len(common_words)) + ' common words in ' + f'{elapsed_time:.2f}' + ' seconds.')

  return common_words


def print_loading(loading):
  loading_text = ["Loading.  ", "Loading.. ", "Loading..."]
  x=0
  while(loading()):
    sys.stdout.write(loading_text[x] + "\r")
    time.sleep(1)
    if x < 2:
      x+=1
    else:
      x=0


# returns known words
def known(words, all_words):
  global dict_letters
  known_words = []
  for word in set(words):
    if word[:2] in letters_list:
      if word[:2] != "zs":
        next_letter_index = letters_list.index(word[:2]) + 1
        next_letter = letters_list[next_letter_index]
        if word in all_words[dict_letters[word[:2]] : dict_letters[next_letter]]:
          known_words.append(word)
      elif word in all_words[dict_letters[word[:2]]:]:
        known_words.append(word)
  return set(known_words)


# get indexes of first letters in all words
def indexes_by_letter(all_words):
  start_time = time.time()
  for letter1 in alphabet:
    letters_list.append(letter1)
    for letter2 in alphabet:
      if letter1 + letter2 in all_words:
        letters_list.append(letter1 + letter2)
  
  local_dict_letters = {letters: all_words.index(letters) for letters in letters_list}
  end_time = time.time()
  elapsed_time = end_time - start_time
  print(f"Time to load indexes: {elapsed_time} seconds")

  return local_dict_letters


# get all possible single level changes to the text
def edits(text):
  split = [(text[:x], text[x:]) for x in range(len(text) + 1)]
  inserts = [x + letter + y for x, y in split for letter in alphabet] # inserts letter at each position
  replaces = [x + letter + y[1:] for x, y in split if y for letter in alphabet] # replaces each letter
  deletes = [x + y[1:] for x, y in split if y] # deletes each letter
  swaps = [x + y[1] + y[0] + y[2:] for x, y in split if len(y) > 1] # swaps each letter
  
  return set(inserts + replaces + deletes + swaps)


def suggest(text, all_words, common_words):
  text = text.lower()
  for char in text:
    if char in punctuation_marks:
      text = text.replace(char, "")

  if text in all_words:
    print(text + ' is a word')
    return
  else:
    print(text + ' is not a word')
    if " " in text:
      sys.stdout.write("Please wait \r")
      suggest_sentences(text, all_words, common_words)
    else:
      sys.stdout.write("Please wait \r")
      suggestions = suggest_words(text, all_words, common_words)
      
      top_suggestions = ", ".join(suggestions.keys())
      if top_suggestions:
        print(f"Suggestions: {top_suggestions}")


# get suggestions for individual words
def suggest_words(text, all_words, common_words):
  suggestions_dict = {}

  suggestions = known(edits(text), all_words) or known([edit2 for edit1 in edits(text) for edit2 in edits(edit1)], all_words) or [text] # take lowest level of edits

  for suggestion in suggestions:
    # get most common words
    if suggestion in common_words:
      suggestions_dict[suggestion] = common_words.index(suggestion)
    else:
      suggestions_dict[suggestion] = 1000000

  sorted_suggestions = dict(sorted(suggestions_dict.items(), key = itemgetter(1))[:3]) # sort in order of how common they are

  return sorted_suggestions


# From Stack Overflow
# spawn threads to check words
def check_words_threads(f, word, all_words, common_words):
  results = [threading.Event(), None]
  def run_func():
    results[1] = f(word, all_words, common_words)
    results[0].set() # set flag to true once function is complete
  threading.Thread(target=run_func).start() # start thread
  return results

# gather all suggestions once threads are completed
def gather_suggestions(suggestions):
  results = []
  for x in range(len(suggestions)):
    suggestions[x][0].wait() # wait for thread to finish
    results.append(suggestions[x][1])
  return results


def suggest_sentences(text, all_words, common_words):
  words = [text]
  misspelled_words = []
  words = words[0].split()
  suggested_sentence = [" "] * len(words)
  x=0
  for word in words:
    # save correctly spelled words
    if word in all_words:
      suggested_sentence[x] = word # save correctly spelled words in same order
    else:
      misspelled_words.append(word) # save misspelled words
    x+=1

  suggestions_threading = [check_words_threads(suggest_words, word, all_words, common_words) for word in misspelled_words] # start threads to get suggestions
  suggestions_dict = gather_suggestions(suggestions_threading) # wait for threads to complete
  
  for suggested_words in suggestions_dict:
    try:
      suggested_words_list = list(suggested_words.keys())
      suggested_sentence[suggested_sentence.index(" ")] = suggested_words_list[0] # save top suggestion in first space found
    except:
      print("An error occurred")
  
  if suggested_sentence[0] in question_words:
    punctuation = "?"
  else:
    punctuation = "."    

  print("Suggestion: " + " ".join(suggested_sentence) + punctuation)


def main():
    global dict_letters
    loading_thread = threading.Thread(target = print_loading, args = (lambda : loading, ))
    all_words = load_words()
    common_words = load_common_words()
    print()
    loading = True
    loading_thread.start()
    dict_letters = indexes_by_letter(all_words)
    loading = False
    print('Type some text, or type \"quit\" to stop')
    while True:
        print()
        text = input(':> ')
        if ('quit' == text):
          break
        suggest(text, all_words, common_words)

if __name__ == "__main__":
    main()

