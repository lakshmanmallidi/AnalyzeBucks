from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans as kmeans
from warnings import catch_warnings,filterwarnings
from re import search
def findstem(arr):
    result = []
    for x in range(len(arr)):
        subparts = arr[x].split(" ")
        for i in range(len(subparts)):
            for j in range(i+1, len(subparts)+1):
                part = " ".join(subparts[i:j])
                count = 0
                for y in range(len(arr)):
                    if (part in arr[y]) and (x != y):
                        count = count+1
                result.append((count, part))
    maxval = 0
    result_str = ""
    for count, str_part in result:
        if(count > maxval):
            maxval = count
            result_str = str_part
        elif(count == maxval and len(str_part) > len(result_str)):
            result_str = str_part
    return result_str

def segregate(transaction_details, n):
    convergence_warning = None
    vectorizer = CountVectorizer()
    vector = vectorizer.fit_transform(transaction_details)
    word_counts = vector.toarray()
    k_means = kmeans(n_clusters=n)
    try:
        with catch_warnings():
            filterwarnings('error')
            try:
                k_means.fit(word_counts)
            except Warning as w:
                convergence_warning = str(w).split(".")[0]
            cluster_ids = k_means.labels_
        unique_clustor_ids = set(cluster_ids)
        unique_clusters = {}
        for clustor_id in unique_clustor_ids:
            common_words = []
            for j in range(len(cluster_ids)):
                if(clustor_id == cluster_ids[j]):
                    common_words.append(transaction_details[j])
            unique_clusters.update({clustor_id: findstem(list(set(common_words)))})
        clusters = []
        for clustor_id in cluster_ids:
            clusters.append((clustor_id, unique_clusters[clustor_id]))
        return (clusters,convergence_warning)
    except Exception:
        convergence_warning = "Enable to find "+str(n)+" clusters"
    return ([],convergence_warning)