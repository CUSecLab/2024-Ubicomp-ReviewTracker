import fasttext
import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix


LEMMATIZER = WordNetLemmatizer()


def preprocess(text):
    return lemmatize_tokens(remove_stop_words(text.lower()))


def remove_stop_words(text):
    with open('stopwords.txt', 'r') as f:
        stop_words = set(f.read().splitlines())
    tokens = word_tokenize(text)
    filtered_tokens = [
        token for token in tokens if token.lower() not in stop_words]
    return filtered_tokens


def lemmatize_tokens(tokens):
    lemmatized_tokens = [LEMMATIZER.lemmatize(token) for token in tokens]
    return " ".join(lemmatized_tokens)


class FastTextEstimator(BaseEstimator, ClassifierMixin):
    def __init__(self, lr=0.1, dim=100, epoch=25):
        self.lr = lr
        self.dim = dim
        self.epoch = epoch

    def fit(self, X, y):
        # Preprocess the data
        X_processed = [preprocess(text) for text in X]
        y_processed = ["__label__" + str(label) for label in y]

        # Save the preprocessed data to a new file
        train_data = pd.DataFrame({"text": X_processed, "label": y_processed})
        train_data.to_csv("train_data_preprocessed.txt",
                          index=False, sep=" ", header=False)

        # Train the FastText classifier
        self.classifier = fasttext.train_supervised(
            "train_data_preprocessed.txt", lr=self.lr, dim=self.dim, epoch=self.epoch
        )

    def predict(self, X):
        # Preprocess the test data
        X_processed = [preprocess(text) for text in X]

        # Make predictions on the test data
        predictions = [self.classifier.predict(x)[0][0].replace(
            "__label__", "") for x in X_processed]

        return predictions

    def predict1(self, X, threshold):

        # Make predictions on the test data and append None for low confidence predictions
        predictions = []
        for x in X:
            pred_label, pred_prob = self.classifier.predict(x)
            pred_prob = pred_prob[0]
            if pred_prob >= threshold:
                pred_label = pred_label[0].replace("__label__", "")
                predictions.append(pred_label)
            else:
                predictions.append(None)

        return predictions

    def score(self, X, y):
        # Make predictions on the test data
        predictions = self.predict(X)

        # Calculate the accuracy of the classifier
        accuracy = sum(predictions == y) / len(y)

        return accuracy

    def score1(self, X, y):

        predictions = self.predict(X)

        accuracy = accuracy_score(y, predictions)

        labels = sorted(set(y))
        precision, recall, f1, _ = precision_recall_fscore_support(
            y, predictions, labels=labels, average=None)

        print("Label\tPrecision\tRecall\t\tF1-score")
        for i, label in enumerate(labels):
            print("{}\t{:.3f}\t\t{:.3f}\t\t{:.3f}".format(
                label, precision[i], recall[i], f1[i]))

        # Print the overall evaluation metrics
        print("Accuracy: {:.3f}".format(accuracy))
        print("Confusion matrix:")
        print(confusion_matrix(y, predictions, labels=labels))

        return accuracy


# Load the data
df = pd.read_csv("data.csv", encoding='unicode_escape')

X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"], test_size=0.1)

# Train the FastText classifier with cross-validation
classifier = FastTextEstimator(lr=0.5, dim=800, epoch=500)
# classifier = FastTextEstimator(lr=0.5, dim=100, epoch=300)
scores = cross_val_score(classifier, X_train, y_train, cv=10)


print("Accuracy: {:.3f} (+/- {:.3f})".format(scores.mean(), scores.std() * 2))
