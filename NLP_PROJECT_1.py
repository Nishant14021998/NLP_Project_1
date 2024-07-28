import pandas as pd
import re
from ftfy import fix_text
from unidecode import unidecode
from collections import Counter
import spacy

# Set year of awards
master_year = 2013

# Import data from json file
json_file_path = "gg2013.json"

try:
    df = pd.read_json(json_file_path)
    print("Data loaded successfully.")
except Exception as e:
    print(f"Error loading data: {e}")

text = df['text'].tolist()

for i, tweet in enumerate(text):
    text[i] = fix_text(tweet)
    text[i] = unidecode(text[i])
    text[i] = " ".join(text[i].split())

spacy_model = spacy.load('en_core_web_sm')
print("SpaCy model loaded successfully.")

#### FIND NAME CLASS #####

def find_name(tweet, candidates):
    doc = spacy_model(tweet)
    for ent in doc.ents:
        if ent.label_ == 'PERSON':
            name = ent.text
            if name in candidates:
                candidates[name] += 1
            else:
                candidates[name] = 1

#### FIND TITLE CLASS ####

def find_title(tweet, candidates, pattern, position):
    var = re.findall(r"(.+?) " + pattern + " (.+)", tweet)
    if var:
        if position == "before":
            titles = var[0][0].rsplit(None, var[0][0].count(' '))
            for i in range(len(titles)):
                candidate = titles[-1]
                if i == 0:
                    if candidate in candidates:
                        candidates[candidate] += 1
                    else:
                        candidates[candidate] = 1
                else:
                    for j in range(i):
                        candidate = titles[-2 - j] + " " + candidate
                        if candidate in candidates:
                            candidates[candidate] += 1
                        else:
                            candidates[candidate] = 1
        elif position == "after":
            titles = var[0][1].split()
            for i in range(len(titles)):
                candidate = titles[0]
                if i == 0:
                    if candidate in candidates:
                        candidates[candidate] += 1
                    else:
                        candidates[candidate] = 1
                else:
                    for j in range(i):
                        candidate = candidate + " " + titles[1 + j]
                        if candidate in candidates:
                            candidates[candidate] += 1
                        else:
                            candidates[candidate] = 1

###### HOST NAMES #####

def get_hosts():
    hosts_candidates = [{}]
    host_pattern = '(hosts?|Hosts?|HOSTS?|hosted by)'
    tweets_of_interest = df.text[df.text.str.contains(host_pattern, regex=True)].tolist()
    print(f"Found {len(tweets_of_interest)} tweets mentioning hosts.")
    
    for tweet in tweets_of_interest:
        if 'next year' in tweet:
            continue
        find_name(tweet, hosts_candidates[0])

    hosts_candidates[0] = Counter(hosts_candidates[0])
    hosts_ordered = hosts_candidates[0].most_common(len(hosts_candidates[0]))
    max_count = hosts_ordered[0][1]
    hosts_candidates = []
    for i in range(len(hosts_ordered)):
        if hosts_ordered[i][1] > max_count * 0.5:
            hosts_candidates.append(hosts_ordered[i][0])
        else:
            break
    return hosts_candidates

####### AWARD NAMES #####

def get_award_names():
    award_names_candidates = []
    current_index = -1
    before_exprs = ['(goes to|Goes To|GOES TO)', '(presenters?|Presenters?|PRESENTERS?|presented by|present(ed|s|ing))']
    after_exprs = ['(wins|Wins|WINS|receiv(es|ed)|won)(?= best|Best|BEST)', '(best(.+?)|Best(.+?)|BEST(.+?))', '(is nominated|nominees for|nominees of)']
    
    for expr in before_exprs:
        tweets_of_interest = df.text[df.text.str.contains(expr, regex=True)].tolist()
        for tweet in tweets_of_interest:
            var = re.findall(r"(.+?) " + expr + " (.+)", tweet)
            if var:
                before = var[0][0].rsplit(None, var[0][0].count(' '))
                for i in range(len(before)):
                    candidate = before[-1]
                    if i == 0:
                        award_names_candidates.append([before[-1]])
                        current_index += 1
                    else:
                        for j in range(i):
                            if "#" in before[-2 - j]:
                                break
                            candidate = before[-2 - j] + " " + candidate
                            if 'best' not in candidate and 'Best' not in candidate:
                                continue
                            award_names_candidates[current_index].append(candidate)
    
    for expr in after_exprs:
        tweets_of_interest = df.text[df.text.str.contains(expr, regex=True)].tolist()
        for tweet in tweets_of_interest:
            var = re.findall(r"(.+?) " + expr + " (.+)", tweet)
            if var and len(var[0]) > 3:
                after = var[0][2].rsplit(None, var[0][0].count(' '))
                for i in range(len(after)):
                    candidate = after[0]
                    if i == 0:
                        if 'best' not in after[0]:
                            break
                        award_names_candidates.append([after[0]])
                        current_index += 1
                    else:
                        for j in range(i):
                            if "#" in after[1 + j]:
                                break
                            candidate = candidate + " " + after[1 + j]
                            if 'best' not in candidate and 'Best' not in candidate:
                                continue
                            award_names_candidates[current_index].append(candidate)
    
    merged_awards = {}
    final_award_candidates = []
    for award_list in award_names_candidates:
        for award in award_list:
            if ('best' in award.split(' ', 1)[0] or 'Best' in award.split(' ', 1)[0]):
                if award in merged_awards:
                    merged_awards[award] += 1
                else:
                    merged_awards[award] = 1
    
    merged_awards = Counter(merged_awards)
    sorted_merged_awards = merged_awards.most_common(len(merged_awards))
    too_far = 1
    max_count = sorted_merged_awards[0][1]
    for j in range(1, len(sorted_merged_awards)):
        if too_far < 20 and sorted_merged_awards[j][1] > max_count * 0.05:
            final_award_candidates.append(sorted_merged_awards[j][0])
            too_far += 1
    
    return final_award_candidates

#### CREATING A DICTIONARY INCLUDING KEYWORDS FOR FINAL AWARD NAMES #####

def get_keywords_from_awards(award_names):
    key_award_words = {}
    for award in award_names:
        key_award_words[award] = []
        for tok in spacy_model(award):
            if tok.pos_ in {"NOUN", "ADJ", "VERB"}:
                key_award_words[award].append(str(tok))
    return key_award_words

#### AWARD PRESENTERS #####

def get_presenters_gold(award_names, key_award_words):
    presenter_candidates = [{} for _ in range(len(award_names))]
    presenter_pattern = '(presenters?|Presenters?|PRESENTERS?|presented by|present(ed|s|ing))'
    tweets_of_interest = df.text[df.text.str.contains(presenter_pattern, regex=True)].tolist()
    for tweet in tweets_of_interest:
        max_count = 0
        best_i = -1
        best_award = ""
        for i, award in enumerate(award_names):
            count = 0
            for match in key_award_words[award]:
                if match.lower() in tweet.lower():
                    count += 1
            # Move on to next category if not enough matches were found in the tweet
            if count < 2:
                continue
            # Find the best match for the category, and prefer shorter categories if there's a tie
            if count > max_count:
                max_count = count
                best_i = i
                best_award = award
            elif count == max_count:
                if len(award.split()) < len(best_award.split()):
                    max_count = count
                    best_i = i
                    best_award = award

        if best_i == -1:
            continue

        # Reset the names because I'm lazy
        i = best_i
        award = best_award

        find_name(tweet, presenter_candidates[i])
    
    for i in range(len(presenter_candidates)):
        presenter_candidates[i] = Counter(presenter_candidates[i])
        pres_ordered = presenter_candidates[i].most_common(len(presenter_candidates[i]))
        if len(presenter_candidates[i]) > 0:
            presenter_candidates[i] = [pres_ordered[0][0]]
            too_far = 1
            max_count = pres_ordered[0][1]
            for j in range(1, len(pres_ordered)):
                if too_far < 4 and pres_ordered[j][1] > max_count * 0.1:
                    presenter_candidates[i].append(pres_ordered[j][0])
                    too_far += 1
        else:
            presenter_candidates[i] = ["not found"]
    return presenter_candidates

#### NOMINEES #####

def get_nominees_gold(award_names):
    nominees_candidates = [{} for _ in range(len(award_names))]
    nominee_pattern = '(nominees?|Nominees?|NOMINEES?|nominated?)|(wins|Wins|WINS|receiv(es|ed)|won)(?= best|Best|BEST)|(best(.+?)|Best(.+?)|BEST(.+?))(?= goes to|Goes To|GOES TO)'
    tweets_of_interest = df.text[df.text.str.contains(nominee_pattern, regex=True)].tolist()
    for tweet in tweets_of_interest:
        # Figure out if tweet is relevant to award category we are looking at
        max_count = 0
        best_i = -1
        best_award = ""
        for i, award in enumerate(award_names):
            count = 0
            for match in key_award_words[award]:
                if match.lower() in tweet.lower():
                    count += 1
            # Move on to next category if not enough matches were found in the tweet
            if count < 1:
                continue
            # Find the best match for the category, and prefer shorter categories if there's a tie
            if count > max_count:
                max_count = count
                best_i = i
                best_award = award
            elif count == max_count:
                if len(award.split()) < len(best_award.split()):
                    max_count = count
                    best_i = i
                    best_award = award

        if best_i == -1:
            continue

        # Reset the names because I'm lazy
        i = best_i
        award = best_award
        # Determine if we should look for a person or movie titles:
        aw_type = ""
        name_types = ["director", "actor", "actress", "cecil", "demille"]
        for n_t in name_types:
            if n_t in award:
                aw_type = "person"
                break
        
        if aw_type == "person":
            find_name(tweet, nominees_candidates[i])
        else:
            find_title(tweet, nominees_candidates[i], 'is nominated', "before")
            find_title(tweet, nominees_candidates[i], '(nominees for|nominees of)', "before")

    for i in range(len(nominees_candidates)):
        nominees_candidates[i] = Counter(nominees_candidates[i])
        noms_ordered = nominees_candidates[i].most_common(len(nominees_candidates[i]))
        if len(nominees_candidates[i]) > 0:
            nominees_candidates[i] = [noms_ordered[0][0]]
            too_far = 1
            if len(noms_ordered) > 1:
                max_count = noms_ordered[1][1]
            else:
                max_count = noms_ordered[0][1]
            for j in range(1, len(noms_ordered)):
                if too_far < 4 or (too_far < 5 and noms_ordered[j][1] > max_count * 0.1):
                    nominees_candidates[i].append(noms_ordered[j][0])
                    too_far += 1
        else:
            nominees_candidates[i] = ["not found"]
    return nominees_candidates


def get_winners_gold(award_names):
    win_candidates = [{} for i in range(len(award_names))]
    # Filter tweets down to winners only
    win_pattern = '(wins|Wins|WINS|receiv(es|ed)|won)(?= best| Best| BEST)|(best(.+)|Best(.+)|BEST(.+))(?= goes to| Goes To| GOES TO)'
    tweets_of_interest = df.text[df.text.str.contains(win_pattern)].values.tolist()
    for tweet in tweets_of_interest:
        # Figure out if tweet is relevant to award category we are looking at
        max_count = 0
        best_i = -1
        best_award = ""
        for i, award in enumerate(award_names):
            count = 0
            for match in key_award_words[award]:
                if match.lower() in tweet.lower():
                    count += 1
            # Move on to next category if not enough matches were found in the tweet
            if (count < 1):
                continue
            # Find the best match for the category, and prefer shorter categories if there's a tie
            if (count > max_count):
                max_count = count
                best_i = i
                best_award = award
            elif (count == max_count):
                if (len(award.split()) < len(best_award.split())):
                    max_count = count
                    best_i = i
                    best_award = award

        if best_i == -1:
            continue

        # Reset the names because I'm lazy
        i = best_i
        award = best_award
        # Determine if we should look for a person or movie titles:
        aw_type = ""
        name_types = ["director", "actor", "actress", "cecil", "demille"]
        for n_t in name_types:
            if n_t in award:
                aw_type = "person"
                break

        before_win_expr = '(wins|Wins|WINS|receiv(es|ed)|won)'
        after_win_expr = '(goes to| Goes To| GOES TO)'
        if (aw_type == "person"):
            find_name(tweet, win_candidates[i])
        else:
            find_title(tweet, win_candidates[i], before_win_expr, "before")
            find_title(tweet, win_candidates[i], after_win_expr, "after")

    #print(win_candidates)
    for i in range(len(win_candidates)):
        win_candidates[i] = Counter(win_candidates[i])
        if len(win_candidates[i]) > 0:
            win_candidates[i] = win_candidates[i].most_common(1)[0][0]
        else:
            win_candidates[i] = "not found"
    #print(win_candidates)
    return win_candidates


# Sample calls to the functions
hosts = get_hosts()
award_names = get_award_names()
key_award_words = get_keywords_from_awards(award_names)
presenters = get_presenters_gold(award_names, key_award_words)
nominees = get_nominees_gold(award_names)
winners = get_winners_gold(award_names)


print("Hosts:", hosts)
print("Award Names:", award_names)
print("Presenters:", presenters)
print("Nominees:", nominees)
print("Winners:",winners)