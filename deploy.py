from flask import Flask, render_template, url_for, request, redirect
import bs4 as bs  
import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
import heapq
import stop_words
import wikipedia
import requests
from nltk.corpus import wordnet
import os
stop_words = stop_words.stopWords
app = Flask(__name__)
num_of_lines = 5
@app.route("/", methods=["GET", "POST"])
def home():
    global summary, topic, num_of_lines, text, url, summary_type
    if request.method == 'GET':
        return render_template("home.html")
    elif request.method == "POST":
        if ("summary_type" in request.form.keys()):
            summary_type = request.form["summary_type"]
            return render_template("home.html", summary_type=summary_type)
        else:
            print("no summary")
        if (summary_type == "topic"):
            try:
                request.form["topic_value"]
                topic = request.form["topic_value"]
                request.form["num_of_lines"]
                num_of_lines = request.form["num_of_lines"]
                summary = main(summary_type, topic, num_of_lines, "", "")
                return render_template('home.html', summary=summary)
            except:
                summary = main(summary_type, topic, num_of_lines, "", "")
                return render_template('home.html', summary=summary)
        elif (summary_type == "text"):
            try:
                request.form["text"]
                text = request.form["text"]
                topic = request.form["text_topic"]
                num_of_lines = request.form["num_of_lines"]
                summary = main(summary_type, topic, num_of_lines, text, "")
                return render_template("home.html", summary=summary)
            except:
                summary = main(summary_type, topic, num_of_lines, text, "")
                return render_template("home.html", summary=summary)
        else:
            try:
                request.form["url"]
                url = request.form["url"]
                topic = request.form["url_topic"]
                num_of_lines = request.form["num_of_lines"]
                summary = main(summary_type, topic, num_of_lines, "", url)
                return render_template("summary.html", summary=summary)
            except:
                summary = main(summary_type, topic, num_of_lines, "", url)
                return render_template("summary.html", summary=summary)    

# Converts the topic url to text by parsing through html
def scrape_page():
    global article, formatted_text, paragraphs
    scraped_page = requests.get(url)
    article = scraped_page.text
    parsed_article = bs.BeautifulSoup(article,'lxml')
    paragraphs = parsed_article.find_all('p')
    text = ""
    for p in paragraphs:  
        text += p.text
    article = re.sub(r'\s+', ' ', text)
    formatted_text = re.sub('[^a-zA-Z]', " ", article)
    formatted_text = re.sub(r'\s+', " ", formatted_text)

    
def topic_to_text(topic):
    global article, formatted_text, paragraphs, url
    topic_ask = topic
    url = wikipedia.page(topic_ask).url
    scrape_page()
   

# Tokenizes the text into words and sentences
def tokenize():
    global sentences, words
    sentences = sent_tokenize(article)
    words = word_tokenize(formatted_text)

""" Creates a dictionary of important words with the keys as 
  words and values as their relative frequencies. """
def word_frequency_dict_creator():
    global word_frequency_dictionary
    word_frequency_dictionary = dict() # Dictionary of words and their frequencies
    for word in words:
        if word not in stop_words:
            if word not in word_frequency_dictionary.keys():
                word_frequency_dictionary[word] = 1
            else:
                word_frequency_dictionary[word] += 1
    max_frequency = max(word_frequency_dictionary.values())
    
    # Relative frequency of words in the frequency dictionary
    for word in word_frequency_dictionary:
        word_frequency_dictionary[word] = word_frequency_dictionary[word]/max_frequency

#Creates a dictionary of sentences and their scores based on the word frequency
def sentence_freq_score_calculator(sentences):
    global sentencevalue
    sentencevalue = dict()

    for sentence in sentences:
        tokenized_list = nltk.word_tokenize(sentence)
        for word in tokenized_list:
            word_freq_keys = word_frequency_dictionary.keys()
            if word in word_freq_keys:
                    if sentence not in sentencevalue:
                        sentencevalue.update({sentence : word_frequency_dictionary[word]})
                    else:
                        sentencevalue[sentence] += word_frequency_dictionary[word]
    return sentencevalue

# Updates the dictionary sentence score values based on other parameters
def sentence_value_updater(topic_ask): 
    sentencevalue = sentence_freq_score_calculator(sentences)
    for sentence in sentencevalue:
        # for each word in topic_ask check
        if topic_ask.lower() + "is" in sentence.lower():
            sentencevalue[sentence] += 4
    
        elif sentences.index(sentence) < 2:
            sentencevalue[sentence] += 23
        elif topic_ask.lower() in sentence.lower(): 
            sentencevalue[sentence] += 3


# Creates a summary based on how many sentences the user would like it to be.            
def summary_creator(num_of_lines):
    n = int(num_of_lines)
    summary = ''
    summary_sentences = heapq.nlargest(n,sentencevalue,key = sentencevalue.get)
    summary = " ".join(summary_sentences)
    summary =  re.sub(r'\[[0-9]*\]'," ", summary)
    summary = re.sub(r'\s+', ' ', summary)
    return summary
   
def main(summary_type, topic, num_of_lines, text, url_string):
    global topic_ask, url
    if summary_type == "topic":
        topic_to_text(topic)
        tokenize()
        word_frequency_dict_creator()
        sentence_value_updater(topic)
        summary = summary_creator(num_of_lines)
        return summary
    elif summary_type == "text":
        global article,formatted_text
        topic_ask = topic
        article = text
        formatted_text = re.sub('[^a-zA-Z.]', " ", article)
        formatted_text = re.sub(r'\s+', " ", formatted_text)
        tokenize()
        word_frequency_dict_creator()
        sentence_value_updater(topic)
        summary = summary_creator(num_of_lines)
        return summary
    else:
        url = url_string
        topic_ask = topic
        scrape_page()
        tokenize()
        word_frequency_dict_creator()
        sentence_value_updater(topic)
        summary = summary_creator(num_of_lines)
        return summary

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)