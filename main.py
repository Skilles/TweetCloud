import itertools
import re
import time
from collections import defaultdict
from keys import PUBLIC_KEY, PRIVATE_KEY, ACCESS_KEY, ACCESS_SECRET
import matplotlib.pyplot as plt
import twitter
from wordcloud import WordCloud

TERM = 'GME'
SEARCHES = 200
BLACKLIST = ['rt', 'https', 'for', 'of', 'and', 'co', 'is', 'the', 'it', 'to', 'in', 'this', 'they', 'you', 'me', 'are',
             'that', 'at']

api = twitter.Api(consumer_key=PUBLIC_KEY, consumer_secret=PRIVATE_KEY, access_token_key=ACCESS_KEY,
                  access_token_secret=ACCESS_SECRET)


def h_space(text: str, max_length: int) -> str:
    h_space = ''
    for _ in range(max_length - len(text)):
        h_space += ' '
    return h_space


def h_line(max_length: int) -> str:
    line = ''
    for _ in range(max_length):
        line += '-'
    return line


def parse_tweets(tweets, output=False):
    all_words = []
    for tweet in tweets:
        name, date, text = tweet['user']['screen_name'], tweet['created_at'], tweet['text']

        max_length = max([len(x) for x in [name, date]])

        words = re.findall(r'\w+', text)

        all_words.append(words)
        if output:
            print(f'{h_line(max_length + 4)}\n'
                  f'| {name}{h_space(name, max_length)} |\n'
                  f'| {date}{h_space(date, max_length)} |\n'
                  f'{h_line(len(text) + 4)}\n'
                  f'| {text} |\n'
                  f'{h_line(len(text) + 4)}')
    return list(itertools.chain.from_iterable(all_words))


def generate_heatmap(words, minimum):
    heatmap = {}
    lower_words = [word.lower() for word in words]

    temp = defaultdict(int)

    # Generate frequencies
    for word in lower_words:
        temp[word] += 1

    # Filter
    for word in temp.keys():
        if temp[word] > minimum and len(word) > 1 and word not in BLACKLIST:
            heatmap[word] = temp[word]
    # # Merge upper/lower case
    # temp = heatmap.copy()
    # for word in temp:
    #     if word.lower() in heatmap.keys():
    #         heatmap[word] += heatmap[word.lower()]
    #         heatmap.pop(word.lower())
    return dict(sorted(heatmap.items(), key=lambda x: x[1], reverse=True))


def get_oldest_tweet_id(search):
    min_tweet = min(search, key=lambda x: x['id'])
    return min_tweet['id']


def multi_search(count: int):
    max_id = 0
    temp = []
    for _ in range(count):
        try:
            if max_id > 0:
                search = \
                    api.GetSearch(term=TERM, return_json=True, include_entities=False, lang='en', count=100,
                                  result_type='mixed', max_id=max_id)['statuses']
            else:
                search = \
                    api.GetSearch(term=TERM, return_json=True, include_entities=False, lang='en', result_type='mixed',
                                  count=100)['statuses']
            max_id = get_oldest_tweet_id(search)

            temp.append(search)
        except twitter.TwitterError:
            print('Rate limited!')
            break
    return list(itertools.chain.from_iterable(temp))


def generate_word_cloud(heatmap):
    start_time = time.perf_counter()

    wordcloud = WordCloud(width=5000, height=5000, margin=1, scale=1, min_font_size=1,
                          max_words=1000).generate_from_frequencies(heatmap)
    print(f'Wordcloud generated | Took: {time.perf_counter() - start_time} seconds')

    wordcloud.to_file('cloud.png')

    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.margins(x=0, y=0)
    plt.show()


start_time = time.perf_counter()

search = multi_search(SEARCHES)

print(f'Total Tweets Parsed: {len(search)} | Took: {time.perf_counter() - start_time} seconds')

total_words = parse_tweets(search)
heatmap = generate_heatmap(total_words, 2)

generate_word_cloud(heatmap)