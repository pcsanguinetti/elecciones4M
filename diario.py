import pandas as pd
from newspaper import Article
from newspaper import Config
from pysentimiento import SentimentAnalyzer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

nltk.download("stopwords")
nltk.download('punkt')
analyzer = SentimentAnalyzer()
pd.set_option("display.precision", 4)
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) Gecko/20100101 Firefox/78.0'
config = Config()
config.browser_user_agent = user_agent
config.request_timeout = 10

class Diario:
    def __init__(self, nombre, url, complemento_url=None, tag=None, class_=None):
        self.nombre = nombre
        self.url = url
        self.complemento_url = complemento_url
        self.tag = tag
        self.class_ = class_
    
    def extraer_links(self):
        links = []
        contenido = requests.get(self.url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(contenido.text, 'html.parser')
        elementos = soup.find_all(self.tag, self.class_)
        for elemento in elementos:
            if elemento.a["href"].startswith("https"):
                link = elemento.a["href"]
            else:
                link = self.complemento_url + elemento.a["href"]
            links.append(link)
        return links

    def scrape(self):
        df_temp = pd.DataFrame(columns=["Diario", "Titular", "Pos", "Neg", "Neu", "Extensión", "Link", "Fecha", "Autor", "Recogido", "Obj_link"])
        links = self.extraer_links()
        for link in links:
            a = Link(link, self.nombre)
            df_temp.loc[len(df_temp)] = [a.diario, a.titular, a.sent["POS"], a.sent["NEG"], a.sent["NEU"], a.ext, a.url, a.fecha, a.autor, a.recogido, a]
        return df_temp

class Link():
    def __init__(self, url, diario):
        self.diario = diario
        self.url = url
        self.titular, self.fecha, self.autor, self.recogido = self.extraer_articulo()
        self.sent = analyzer.predict_probas(self.titular)
        self.ext = len(self.titular.split(" "))
        self.cita, self.no_cita = self.cita_o_no()

    def cita_o_no(self):
        texto = re.sub("[“”‘’‛‟„'\"′″´˝`❛❜❝❞‹›«»]", "'", self.titular)
        lista = re.findall("('.*?')", texto)
        cita = " ".join(lista)
        cita = cita.replace("'","")
        cita = re.sub(r'[^\w\s]', '', cita)
        no_cita = re.sub("('.*?')", "", texto)
        no_cita = no_cita.replace("  ", " ")
        no_cita = no_cita.replace("  ", " ")
        no_cita = re.sub(r'[^\w\s]', '', no_cita)
        return cita, no_cita
    
    def extraer_articulo(self):
        recogido = datetime.today().strftime('%d-%m-%y')
        try:
            a = Article(self.url, config=config)
            a.download()
            a.parse()
            fecha = a.publish_date
            fecha = str(fecha)[0:10]
            autor = a.authors
            titular = a.title
            return titular, fecha, autor, recogido
        except:
            return "error", recogido, "error", recogido

def filtrar_belicas(df_in, pattern):
    belicas_temp = pd.DataFrame(columns=["Palabra", "Cita", "Titular", "Diario", "Fecha"])
    for row in df_in.itertuples(index=True, name='Pandas'):
        a = getattr(row, "Obj_link")
        if a.cita != "":
            txt = word_tokenize(a.cita)
            clean = [t.lower() for t in txt if len(t) > 2 and t not in stopwords.words("spanish")]
            for t in clean:
                if re.search(pattern, t):
                    belicas_temp.loc[len(belicas_temp)] = [t, 1, a.titular, a.diario, a.fecha]

        if a.no_cita != "":
            txt = word_tokenize(a.no_cita)
            clean = [t.lower() for t in txt if len(t) > 2 and t not in stopwords.words("spanish")]
            for t in clean:
                if re.search(pattern, t):
                    belicas_temp.loc[len(belicas_temp)] = [t, 0, a.titular, a.diario, a.fecha]
    return belicas_temp

def rearrange(df):
    df_temp = pd.DataFrame(columns=["titular", "diario", "fecha", "todo"])
    for row in df.itertuples(index=True, name='Pandas'):
        titular = getattr(row, "Titular")
        diario = getattr(row, "Diario")
        fecha = getattr(row, "Fecha")
        titular = re.sub(r"([^\w\s])", ' \\1 ', titular)
        titular = re.sub(r"\s+", " ", titular)
        total = titular + " (" + diario + ", " + fecha + ") | "
        df_temp.loc[len(df_temp)] = [titular, diario, fecha, total]
    return df_temp

if __name__ == "__main__":
    main()