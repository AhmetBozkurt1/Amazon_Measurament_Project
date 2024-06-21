##############################################
# Amazon Ürün Puanlaması ve Yorum Sıralaması
##############################################

# İş Problemi
# E-ticarette en önemli sorunlardan biri, ürünlere verilen puanların doğru şekilde hesaplanmasıdır. Bu sorunun çözülmesi,
# e-ticaret siteleri için müşteri memnuniyetini artırırken, satıcılar için ürünlerinin daha fazla dikkat çekmesini ve
# alıcılar için sorunsuz bir alışveriş deneyimi sağlamayı içerir. Bir diğer önemli sorun ise ürünlere verilen yorumların
# doğru bir şekilde sıralanmasıdır. Yanıltıcı yorumların öne çıkması, ürün satışlarını doğrudan etkileyebilir, bu da
# hem maddi kayıplara hem de müşteri kaybına neden olabilir. Bu iki temel sorunun çözülmesi, e-ticaret siteleri ve
# satıcıları için satışları artırırken, müşterilerin sorunsuz bir alışveriş deneyimi yaşamasını sağlar.

# Veri Seti Hikayesi
# Bu veri seti, Amazon ürün verilerini içerir ve çeşitli ürün kategorileri ile ilişkili metadataları içerir. Veri seti
# içerisinde en fazla yoruma sahip olan elektronik kategorisindeki ürünlerin kullanıcı puanları ve yorumları bulunmaktadır.

# Değişkenler:
# reviewerID: Kullanıcı ID’si
# asin: Ürün ID’si
# reviewerName: Kullanıcı Adı
# helpful: Faydalı derecelendirme
# reviewText: İnceleme metni
# overall: Ürün derecesi
# summary: İnceleme özeti
# unixReviewTime: İnceleme zamanı (Unix formatında)
# reviewTime: İnceleme zamanı (Raw)
# day_diff: İncelemeden bu yana geçen gün sayısı
# helpful_yes: Faydalı bulunan inceleme sayısı
# total_vote: İncelemeye verilen toplam oy sayısı

#########################
# PROJE GÖREVLERİ
#########################

import pandas as pd
import math
import datetime as dt
import scipy.stats as st
import warnings
warnings.filterwarnings("ignore")

pd.set_option("display.max_columns", None)
pd.set_option("display.max_row", None)
pd.set_option("display.width", 500)
pd.set_option("display.float.format", lambda x: "%.3f" % x)

# GÖREV 1: Average Rating’i güncel yorumlara göre hesaplayınız ve var olan average rating ile kıyaslayınız.

# Paylaşılan veri setinde kullanıcılar bir ürüne puanlar vermiş ve yorumlar yapmıştır. Bu görevde amacımız verilen
# puanları tarihe göre ağırlıklandırarak değerlendirmek. İlk ortalama puan ile elde edilecek tarihe göre ağırlıklı
# puanın karşılaştırılması gerekmektedir.

# Veri Setini Okutma/İnceleme
df = pd.read_csv("amazon_review.csv")
df.head()
df.shape
df.info()
df.isnull().sum()
df["asin"].nunique()
df["overall"].value_counts()

# Adım 1: Ürünün ortalama puanını hesaplayınız.
df["overall"].mean()  # 4.587589013224822

# Adım 2: Tarihe göre ağırlıklı puan ortalamasını hesaplayınız.

# Tarih değişkeninin dtype değerini datetime çeviriyorum.
df["reviewTime"].dtypes
df["reviewTime"] = df["reviewTime"].apply(lambda x: pd.to_datetime(x))


# NOT: Burada zamanları net olarak ben belirlemedim.Sebebi de, benim verim sürekli güncellenen bir veri ise her zamana
# göre ağırlık baktığımda çeyreklik değerleri güncellemem lazım ama bu fonksiyondaki gibi yazarsam ne kadar veri eklenirse
# eklensin sürekli çeyreklik dilimlerden alacağı için değişikliğe gerek olmayacaktır.

# Zamana göre ağırlıklı puanı belirlemek için fonksiyonumu yazıyorum.
def time_based_weighted_score(dataframe, w1, w2, w3, w4):
    return dataframe.loc[dataframe["day_diff"] <= dataframe["day_diff"].quantile(0.25), "overall"].mean() * w1/100 + \
        dataframe.loc[(dataframe["day_diff"] > dataframe["day_diff"].quantile(0.25))
                      & (dataframe["day_diff"] <= dataframe["day_diff"].quantile(0.5)), "overall"].mean() * w2/100 + \
        dataframe.loc[(dataframe["day_diff"] > dataframe["day_diff"].quantile(0.5))
                      & (dataframe["day_diff"] <= dataframe["day_diff"].quantile(0.75)), "overall"].mean() * w3/100 + \
        dataframe.loc[dataframe["day_diff"] > dataframe["day_diff"].quantile(0.75), "overall"].mean() * w4/100

time_based_weighted_score(df, 32, 26, 22, 20)
# Buradan görüldüğü üzere baştaki ortalamamız 4.5875'ten 4.6031'e yükselmiş.
# Anlıyoruz ki burada ürün geliştirilmiş ve yapılan kötü yorumlar dikkate alınmış.

# Adım 3: Ağırlıklandırılmış puanlamada her bir zaman diliminin ortalamasını karşılaştırıp yorumlayınız.

df.loc[df["day_diff"] <= df["day_diff"].quantile(0.25), "overall"].mean()


df.loc[(df["day_diff"] > df["day_diff"].quantile(0.25))
       & (df["day_diff"] <= df["day_diff"].quantile(0.5)), "overall"].mean()

df.loc[(df["day_diff"] > df["day_diff"].quantile(0.5))
       & (df["day_diff"] <= df["day_diff"].quantile(0.75)), "overall"].mean()

df.loc[df["day_diff"] > df["day_diff"].quantile(0.75), "overall"].mean()

# Anlaşıldığı üzere yakın tarihe doğru ratingde artış gözlenmiştir. Bunun sebepleri yapılan güncellemeler olabilir.


# GÖREV 2: Ürün için ürün detay sayfasında görüntülenecek 20 review’i belirleyiniz.

# Yorumları Sıralama
#Yapılan incelemeleri analiz etmek için 3 yaklaşım vardır. Aşağıda bunları kullanarak açıklayacağım.

# Adım 1: helpful_no değişkeni datasetimde olmadığı için ilk onu üretiyorum.
df["helpful_no"] = df["total_vote"] - df["helpful_yes"]

# 1.YOL
# Up-Down Difference Score
# Basitçe oyların birbirinden farkıdır.

def score_up_down_diff(up, down):
    return up - down

df["score_pos_neg_diff"] = score_up_down_diff(df["helpful_yes"], df["helpful_no"])
#Bu yaklaşımda sorun oyların miktar farklılığından dolayı iki ürünü doğru karşılaştıramayız ve bu sorun çıkarabilir.

# Ortalama Puan
# helpful_yes yüzdesini hesaplayarak bulabiliriz

def score_up_down_rate(up, down):
    if up + down == 0:
        return 0
    return up / (up+down)

df["score_average_rating"] = df.apply(lambda x: score_up_down_rate(x["helpful_yes"], x["helpful_no"]), axis=1)
# Bu da başka bir sorunu beraberinde getirir çünkü bu süreç incelemenin oylama sıklığını göz ardı eder.
# Örneğin, 2 inceleme var: bunlardan ilkinde 2 upvote 0 downvote var ve ikincisinde 100 upvote 1 downvote var.
# Birincisi ikincisinin üstünde sıralanacaktır ancak ikinci inceleme çok daha fazla kullanıcı tarafından onaylandığı
# için çok daha geçerlidir. Bu nedenle, bu gerçek hayat için uygulanabilir ve güvenilir değildir. Bu da bizi
# incelemelerin hem sıklığını hem de yüzdesini dikkate alan 3. yaklaşıma, yani "Wilson Alt Sınır Puanı "na getiriyor.


# Wilson Lower Bound Skoru (WLB Score)
# Sıralama için çok daha teknik bir yaklaşımdır. Bernoulli parametresi (p) için bir güven aralığı hesaplar ve güven
# aralığının alt sınırını WLB Puanı olarak tanımlar.
# Örneğin, bir inceleme 600 olumlu ve 400 olumsuz oy almış olsun. Yukarı oyların yüzdesi %60'tır. Güven aralığı
# hesaplandığında, sonucun [0,5, 0,7] olarak bulunduğunu varsayalım, bu nedenle bu yaklaşım alt sınırı 0,5 olarak
# kabul eder. Bu tüm gözlemler için yapıldığında garantili bir alt skor olduğu söylenebilir, sıralama bu alt skora göre
# yapılabilir. Bu şekilde hem frekans hem de ortalama sıralama algoritmasına dahil edilmiş olur.

def wilson_lower_bound(up, down, confidence=0.95):
    """
    Wilson Lower Bound Score hesapla

    - Bernoulli parametresi p için hesaplanacak güven aralığının alt sınırı WLB skoru olarak kabul edilir.
    - Hesaplanacak skor ürün sıralaması için kullanılır.
    - Not:
    Eğer skorlar 1-5 arasıdaysa 1-3 negatif, 4-5 pozitif olarak işaretlenir ve bernoulli'ye uygun hale getirilebilir.
    Bu beraberinde bazı problemleri de getirir. Bu sebeple bayesian average rating yapmak gerekir.

    Parameters
    ----------
    up: int
        up count
    down: int
        down count
    confidence: float
        confidence

    Returns
    -------
    wilson score: float

    """
    n = up + down
    if n == 0:
        return 0
    z = st.norm.ppf(1 - (1 - confidence) / 2)
    phat = 1.0 * up / n
    return (phat + z * z / (2 * n) - z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)) / (1 + z * z / n)

df["wilson_lower_bound"] = df.apply(lambda x: wilson_lower_bound(x["helpful_yes"], x["helpful_no"]), axis=1)

# Şimdi oluşturduğumuz skorlara göre sıralamalar yapalım ve WLB yaklaşımının ne kadar önemli olduğunu görelim.
# İlk olarak score_average_rating değişkenine göre sıralayalım.
df[["score_average_rating", "helpful_yes", "helpful_no", "wilson_lower_bound"]] \
    .sort_values("score_average_rating", ascending=False).head(10)


# Şimdi de wilson_lower_bound değişkenine göre sıralayalım.
df[["score_average_rating", "helpful_yes", "helpful_no", "wilson_lower_bound"]] \
    .sort_values("wilson_lower_bound", ascending=False).head(10)

# Görüldüğü üzere WLB Score sıklık ve ortalamayı dikkate aldığı için diğerlerine göre çok daha mantıklı bir sıralama
# oluşturmaktadır. Bir incelemenin üst sıralarda yer alabilmesi için yeterli sayıda oy ve up alması gerekmektedir.

#Sonuç:
# Bu projede hem derecelendirmeler hem de sıralama incelemeleri incelenmiştir. İncelemeler için 2 sonuç bulunmaktadır:
# Derecelendirmelerde, ortalama derecelendirme zamanın etkisini göz ardı edebilir, bu nedenle bu etki belirlenmeli ve
# hesaplamaya ağırlık olarak eklenmelidir. Zaman Bazlı Ağırlıklı Ortalama sonucu, aksiyon almak için daha fazla
# şans verebilir. Bir sıralama algoritmasında sadece yukarı/aşağı oyların farkına veya dağılımına bakmak yeterli değildir.
# Hem verilen toplam oylar (frekans) hem de yukarı oyların / aşağı oyların dağılımı (ortalama) dikkate alınabilir.
# Kullanılabilecek en iyi yöntemlerden biri Wilson'ın Alt Sınır Puanıdır. Bu yöntem istatistiklere dayandığından,
# sonuçlar yukarı ve aşağı oyların farkı veya ortalaması gibi sezgisel yöntemlerden daha iyidir.

