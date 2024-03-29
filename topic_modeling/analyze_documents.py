from os import listdir, environ
from os.path import isfile, join, dirname, realpath
from gensim import corpora
from gensim.models import Phrases
from gensim.models.wrappers import LdaMallet
import pandas as pd

ITERATIONS = 100


def create_topic_analytics(lda_model, corpus, documents):
    # Create df to aggregate and display topic breakdown
    topics_df = pd.DataFrame()
    for i, row in enumerate(lda_model[corpus]):
        row = sorted(row, key=lambda x: (x[1]), reverse=True)
        for j, (topic_num, prop_topic) in enumerate(row):
            if j == 0:
                wp = lda_model.show_topic(topic_num)
                topic_keywords = ", ".join([word for word, prop in wp])
                topics_df = topics_df.append(
                    pd.Series([int(topic_num), round(prop_topic, 4), topic_keywords]), ignore_index=True)
    topics_df.columns = ['Dominant_Topic', 'Percentage_Contribution', 'Topic_Keywords']
    contents = pd.Series(documents)
    topics_df = pd.concat([topics_df, contents], axis=1)
    df_topic_keywords = topics_df

    # Create df for dominant topic at document level
    df_dominant_topic = df_topic_keywords.reset_index()
    df_dominant_topic.columns = ['Document_No', 'Dominant_Topic', 'Topic_Percentage_Contrib', 'Keywords', 'Text']

    # Create df for displaying most relevant document for each topic
    df_representative_topic = pd.DataFrame()
    df_topics_grouped = df_topic_keywords.groupby('Dominant_Topic')
    for i, group in df_topics_grouped:
        df_representative_topic = pd.concat([df_representative_topic,
                                                 group.sort_values(['Percentage_Contribution'], ascending=[0]).head(1)],
                                                axis=0)
    df_representative_topic.reset_index(drop=True, inplace=True)
    df_representative_topic.columns = ['Topic_Num', "Topic_Percentage_Contrib", "Keywords", "Text"]

    return df_dominant_topic, df_representative_topic


def build_lda_model(CIKs, num_topics, ngram_num):
    documents = []
    lda_model = None
    dct = None
    corpus = None

    main_path = dirname(realpath(__file__)) + "/data/14d9"
    for CIK in CIKs:
        files = [f for f in listdir(main_path + '/' + CIK) if isfile(join(main_path + '/' + CIK, f))]
        for file in files:
            try:
                with open(main_path + '/' + CIK + '/' + file, "r", encoding="latin-1") as f:
                    for row in f:
                        document = [word for word in row.split(" ") if len(word) > 2]
                        documents.append(document)
            except IOError as e:
                print("Couldn't open file (%s)." % e)

    # Add bigram, trigrams, and quadgrams
    bigram = Phrases(documents)
    documents = [bigram[line] for line in documents]
    trigram = Phrases(documents)
    documents = [trigram[line] for line in documents]
    quadgram = Phrases(documents)
    documents = [quadgram[line] for line in documents]
    documents = list(map(lambda document: list(filter(lambda word: word.count('_') == (ngram_num - 1), document)), documents))

    # Dictionary
    dct = corpora.Dictionary(documents)

    # Corpus
    corpus = [dct.doc2bow(line) for line in documents]

    environ['MALLET_HOME'] = dirname(realpath(__file__)) + '/mallet-2.0.8/'
    mallet_path = dirname(realpath(__file__)) + "/mallet-2.0.8/bin/mallet"
    lda_mallet = LdaMallet(mallet_path, corpus=corpus, num_topics=num_topics, id2word=dct, iterations=ITERATIONS)

    # Show Topics
    print("LDA Model MALLET")
    for idx in range(num_topics):
        print("Topic #%s-" % idx, lda_mallet.print_topic(idx, 10))

    # Format topic and percentage for api export
    formatted_topics = []
    for _, topic_str in lda_mallet.print_topics():
        current_topic = []
        for percent_topic in topic_str.split(' + '):
            percent, term = percent_topic.split('*')
            current_topic.append({'weight': float(percent) * 1000, 'term': term[1:-1]})
        formatted_topics.append(current_topic)

    # Create df for analytics over topics
    df_dominant_topic, df_representative_topic = create_topic_analytics(lda_mallet, corpus, documents)

    return formatted_topics, df_dominant_topic.to_dict('records'), df_representative_topic.to_dict('records')
