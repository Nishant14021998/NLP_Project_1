# NLP_Project_1
# 2013 Golden Globes Tweet Mining NLP Project

## Project Overview
This project focuses on mining tweets related to the 2013 Golden Globes to get information about various categories, namely Hosts, Award Names, Presenters, Nominees, and Winners. The project employs Natural Language Processing (NLP) techniques, such as Regular Expressions (Regex) and Part of Speech (POS) tagging, to accurately identify and categorize relevant information from the tweets.

## Categories
The project gets information from the following five categories:
1. **Hosts**: Identifying the hosts of the event.
2. **Award Names**: Getting the names of the awards presented.
3. **Presenters**: Identifying the individuals who presented the awards.
4. **Nominees**: Getting the names of the nominees for each award.
5. **Winners**: Identifying the winners of the awards.

## Tools and Libraries
The project utilizes the following tools and libraries:
- **NLTK**: For natural language processing and POS tagging.
- **Spacy**: For advanced NLP operations.
- **univdecode**: For decoding text.
- **Regex**: For pattern matching and extraction.
- **pandas**: For data manipulation and analysis.
- **ftfy**: For fixing text encoding issues.
- **unidecode**: For converting Unicode text to ASCII.

## Functions
Separate functions have been created for getting information for each category:
- `get_hosts()`
- `get_award_names()`
- `get_presenters()`
- `get_nominees()`
- `get_winners()`

## Installation
To run this project, you need to have Python installed. You can install the required libraries using the `requirements.txt` file.

